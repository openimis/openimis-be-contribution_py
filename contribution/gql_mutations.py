from contribution.services import premium_updated
from policy.models import Policy
from typing import Optional
import requests
# from paymentap import payment_request

import graphene
from core import filter_validity
from contribution.apps import ContributionConfig
from core.schema import OpenIMISMutation
from .models import Premium, PremiumMutation
from mobile_payment.models import Transactions, PaymentServiceProvider
from payer.models import Payer
from policy import models as policy_models
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext as _
from core import datetime
import logging

logger = logging.getLogger(__name__)



class PaymentServiceProviderInputType(OpenIMISMutation.Input):
    id = graphene.Int(required = False, read_only = True)
    uuid = graphene.String(required=False)
    psp_account = graphene.String (required=True)
    psp_name = graphene.String(required=True)
    psp_pin = graphene.String(required= True)
    is_external_api_user = graphene.Boolean(default = False)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                

class PremiumBase:
    """
    This takes most parameters of the Premium with addition of action. This fields allows to force
    """
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    policy_uuid = graphene.String(required=True)
    payer_uuid = graphene.String()
    transaction_uuid = graphene.String(required=False)
    amount = graphene.Decimal()
    receipt = graphene.String(required=False)      
    pay_date = graphene.Date()
    pay_type = graphene.String(max_length=25)
    is_offline = graphene.Boolean(required=False)
    is_photo_fee = graphene.Boolean(required=False)
    action = graphene.String(required=False)

    # json_ext = graphene.types.json.JSONString(required=False)


    
def reset_wallet_before_udate(wallet):
    wallet.name = None
    wallet.wallet_address = None

    wallet.name = None
    wallet.wallet_address = None

def reset_premium_before_update(premium):
    premium.amount = None
    premium.receipt = None
    premium.policy = None
    premium.payer = None
    premium.pay_date = None
    premium.pay_type = None
    premium.is_photo_fee = None
    premium.is_offline = None
    premium.reporting_id = None





def update_or_create_wallet(data, user):
    # Check if client_mutation_id is passed in data
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    # Check if client_mutation_label is passed in data
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    from core.utils import TimeUtils
    data['validity_from'] = TimeUtils.now()
    # get wallet_uuid from data
    Payment_service_provider_uuid = data.pop("uuid") if "uuid" in data else None
    if Payment_service_provider_uuid:
        # fetch wallet by uuid
        payment_service_provider = PaymentServiceProvider.objects.get(uuid=Payment_service_provider_uuid)
        payment_service_provider.save_history()
        [setattr(payment_service_provider , key, data[key]) for key in data]
    else:
        # create new wallet object
        payment_service_provider  = PaymentServiceProvider.objects.create(**data)
    # save record to database
    payment_service_provider.save()
    return payment_service_provider 

def update_or_create_premium(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    now = datetime.datetime.now()
    # data['audit_user_id'] = user.id_for_audit
    data['validity_from'] = now
    policy_uuid = data.pop("policy_uuid") if "policy_uuid" in data else None
    if not policy_uuid:
        raise Exception(_("policy_uuid_required"))
    policy = Policy.filter_queryset(None).filter(uuid=policy_uuid).first()
    if not policy:
        raise Exception(_("policy_uuid_not_found") % (policy_uuid,))
    data["policy"] = policy
    # TODO verify that the user has access to specified payer_id
    premium_uuid = data.pop("uuid") if "uuid" in data else None
    # action: enforce, suspend, wait
    action = data.pop("action") if "action" in data else None
    payer_uuid = data.pop("payer_uuid") if "payer_uuid" in data else None
    payer = Payer.filter_queryset().filter(uuid=payer_uuid).first() if payer_uuid else None
    # pop transaction_uuid from the input data
    transaction_uuid = data.pop("transaction_uuid") if "transaction_uuid" in data else None
    # fetch transactions_uuid from the database and compare it with the one inputed from graphql
    transaction = Transactions.filter_queryset().filter(uuid=transaction_uuid).first() if transaction_uuid else None
    #checks if the transaction inputed exist in the databse if not it raise exception of not foun
    data["transaction"] = transaction
    if premium_uuid:
        premium = Premium.objects.get(uuid=premium_uuid)
        premium.save_history()
        reset_premium_before_update(premium)
        [setattr(premium, k, v) for k, v in data.items()]

        if payer_uuid and payer:
            premium.payer = payer
        premium.save()
    else:
        premium = Premium.objects.create(**data)
    if payer_uuid and payer:
        premium.payer = payer
        premium.save()
    # Handle the policy updating
    premium_updated(premium, action)
    return premium

class CreatePaymentServiceProvider(OpenIMISMutation):
    """
    Add a Merchant wallet address for mobile money payment
    """
    _mutation_module = "contribution"
    _mutation_class = "CreatePaymentServiceProvider"

    class Input(PaymentServiceProviderInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data)  -> Optional[str]: 
        try:
            
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                _("mutation.authentication_required"))
            #checks if user has permission to create a wallet
            if not user.has_perms(ContributionConfig.gql_mutation_create_paymnet_service_provider):
                raise PermissionDenied(_("unauthorized"))
            client_mutation_id = data.get("client_mutation_id")
            # it create data inputs from the premium graphql
            payment_service_provider = update_or_create_wallet(data, user)
            PaymentServiceProviderMutation.object_mutated(user, client_mutation_id=client_mutation_id, payment_service_provider=payment_service_provider)
            return None
        except Exception as exc:
            logger.debug("Exception when deleting premium %s", exc_info=exc)
            return [{
                'message': _("wallet.mutation.failed_to_create_wallet"),
                'detail': str(exc)}
            ]


class UpdatePaymentServiceProvider(OpenIMISMutation):
    _mutation_module = "contribution"
    _mutation_class = "UpdatePaymentServiceProvider"


    class Input (PaymentServiceProviderInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):

        try:
            if not user.has_perms(ContributionConfig.gql_mutation_update_paymnet_service_provider):
                raise PermissionDenied(_("unauthorized"))
            #get merchant uuid
            payment_service_provider_uuid = data.pop('uuid')
            if payment_service_provider_uuid:
                #fetch merchnat uuid from database
                payment_service_provider = PaymentServiceProvider.objects.get(uuid = payment_service_provider_uuid)
                [setattr(payment_service_provider, key, data[key]) for key in data]
            else:
                 #raise an error if uuid is not valid or does not exist
                 raise PermissionDenied(_("unauthorized"))
            #saves update dta
            payment_service_provider.save()
            return None
        except Exception as exc:
            return [{
                
                'message': _("wallet.mutation.failed_to_update_wallet"),
                'detail': str(exc)}]


class DeletePaymentServiceProvider(OpenIMISMutation):

    _mutation_module = 'contribution'
    _mutation_class = 'DeletePaymentServiceProvider'


    class Input(OpenIMISMutation.Input):
        uuid = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):

        try:
             # Check if user has permission
            if not user.has_perms(ContributionConfig.gql_mutation_delete_paymnet_service_provider):
                raise PermissionDenied(_("unauthorized"))
            
             # get programs object by uuid
            payment_service_provider = PaymentServiceProvider.objects.get(uuid=data['uuid'])

            # get current date time
            from core import datetime
            now = datetime.datetime.now()

            # Set validity_to to now to make the record invalid
            payment_service_provider.validity_to = now
            payment_service_provider.save()
            return None
        except Exception as exc:
            return [{
                'message': "Faild to delete Wallet. An exception had occured",
                'detail': str(exc)}]



class CreatePremiumMutation(OpenIMISMutation):
    """
    Create a contribution for policy with or without a payer
    """
    _mutation_module = "contribution"
    _mutation_class = "CreatePremiumMutation"

    class Input(PremiumBase, OpenIMISMutation.Input):
        pass

    @classmethod
    def async_mutate(cls, user, **data) -> Optional[str]:
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(ContributionConfig.gql_mutation_create_premiums_perms):
                raise PermissionDenied(_("unauthorized"))
            client_mutation_id = data.get("client_mutation_id")
            premium = update_or_create_premium(data, user)
            print(data)
            PremiumMutation.object_mutated(user, client_mutation_id=client_mutation_id, premium=premium)
            return None
        except Exception as exc:
            return [{
                'message': _("contribution.mutation.failed_to_create_premium"),
                'detail': str(exc)}
            ]

class UpdatePremiumMutation(OpenIMISMutation):
    """
    Update a contribution for policy with or without a payer
    """
    _mutation_module = "contribution"
    _mutation_class = "UpdatePremiumMutation"

    class Input(PremiumBase, OpenIMISMutation.Input):
        pass

    @classmethod
    def async_mutate(cls, user, **data) -> Optional[str]:
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(ContributionConfig.gql_mutation_update_premiums_perms):
                raise PermissionDenied(_("unauthorized"))
            update_or_create_premium(data, user)
            return None
        except Exception as exc:
            return [{
                'message': _("contribution.mutation.failed_to_update_premium") %
                           {'id': data.get('id') if data else None},
                'detail': str(exc)}
            ]


class DeletePremiumsMutation(OpenIMISMutation):
    """
    Delete one or several Premiums.
    """
    _mutation_module = "contribution"
    _mutation_class = "DeletePremiumsMutation"

    class Input(OpenIMISMutation.Input):
        uuids = graphene.List(graphene.String)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(ContributionConfig.gql_mutation_delete_premiums_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = []
        for premium_uuid in data["uuids"]:
            premium = Premium.objects \
                .filter(uuid=premium_uuid) \
                .first()
            if premium is None:
                errors.append({
                    'title': premium_uuid,
                    'list': [{'message': _(
                        "contribution.validation.id_does_not_exist") % {'id': premium_uuid}}]
                })
                continue
            errors += set_premium_deleted(premium)
        if len(errors) == 1:
            errors = errors[0]['list']
        return errors


def set_premium_deleted(premium):
    try:
        premium.delete_history()
        return []
    except Exception as exc:
        logger.debug("Exception when deleting premium %s", premium.uuid, exc_info=exc)
        return {
            'title': premium.uuid,
            'list': [{
                'message': _("contribution.mutation.failed_to_delete_premium") % {'uuid': premium.uuid},
                'detail': premium.uuid}]
        }


def on_policy_mutation(sender, **kwargs):
    errors = []
    if kwargs.get("mutation_class") == 'DeletePoliciesMutation':
        uuids = kwargs['data'].get('uuids', [])
        policies = policy_models.Policy.objects.prefetch_related("premiums").filter(uuid__in=uuids).all()
        for policy in policies:
            for premium in policy.premiums.all():
                errors += set_premium_deleted(premium)
    return errors


def on_premium_mutation(sender, **kwargs):
    uuids = kwargs['data'].get('uuids', [])
    if not uuids:
        uuid = kwargs['data'].get('uuid', None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_premiums = Premium.objects.filter(uuid__in=uuids).all()
    for premium in impacted_premiums:
        PremiumMutation.objects.update_or_create(premium=premium, mutation_id=kwargs['mutation_log_id'])
    return []
