import logging
from urlparse import urljoin
from xml.etree import ElementTree

from recurly.resource import Resource
from . import js  # noqa


"""
Recurly's Python client library is an interface to its REST API.
Please see the Recurly API documentation for more information:
http://docs.recurly.com/api/
"""


__version__ = '2.1.7'

BASE_URI = 'https://api.recurly.com/v2/'
"""The API endpoint to send requests to."""

API_KEY = None
"""The API key to use when authenticating API requests."""

CA_CERTS_FILE = None
"""A file contianing a set of concatenated certificate authority certs
for validating the server against."""

DEFAULT_CURRENCY = 'USD'
"""The currency to use creating `Money` instances when one is not specified."""


class Account(Resource):

    """A customer account."""

    member_path = 'accounts/%s'
    collection_path = 'accounts'

    nodename = 'account'

    attributes = (
        'account_code',
        'billing_info',
        'state',
        'username',
        'email',
        'first_name',
        'last_name',
        'company_name',
        'accept_language',
        'hosted_login_token',
        'created_at',
    )
    sensitive_attributes = ('number', 'verification_value',)
    linked_attributes = (
        'adjustments',
        'billing_info',
        'invoices',
        'redemption',
        'subscriptions',
        'transactions',
    )
    js_attributes = (
        'account_code',
        'username',
        'email',
        'first_name',
        'last_name',
        'company_name',
    )

    def to_element(self, full=False):
        elem = super(Account, self).to_element(full=full)

        # Make sure the account code is always included in a serialization.
        if 'account_code' not in self.__dict__:  # not already included
            try:
                account_code = self.account_code
            except AttributeError:
                pass
            else:
                elem.append(
                    self.element_for_value('account_code', account_code))

        if 'billing_info' in self.__dict__:
            elem.append(self.billing_info.to_element())
        return elem

    @classmethod
    def all_active(cls, **kwargs):
        """Return a `Page` of active customer accounts.

        This is a convenience method for `Account.all(state='active')`.

        """
        return cls.all(state='active', **kwargs)

    @classmethod
    def all_closed(cls, **kwargs):
        """Return a `Page` of closed customer accounts.

        This is a convenience method for `Account.all(state='closed')`.

        """
        return cls.all(state='closed', **kwargs)

    @classmethod
    def all_past_due(cls, **kwargs):
        """Return a `Page` of past-due customer accounts.

        This is a convenience method for `Account.all(state='past_due').

        """
        return cls.all(state='past_due', **kwargs)

    @classmethod
    def all_subscribers(cls, **kwargs):
        """Return a `Page` of customer accounts that are subscribers.

        This is a convenience method for `Account.all(state='subscriber').

        """
        return cls.all(state='subscriber', **kwargs)

    @classmethod
    def all_non_subscribers(cls, **kwargs):
        """Return a `Page` of customer accounts that are not subscribers.

        This is a convenience method for `Account.all(state='non_subscriber').

        """
        return cls.all(state='non_subscriber', **kwargs)

    def __getattr__(self, name):
        if name == 'billing_info':
            try:
                billing_info_url = \
                    self._elem.find('billing_info').attrib['href']
            except (AttributeError, KeyError):
                raise AttributeError(name)
            resp, elem = BillingInfo.element_for_url(billing_info_url)
            return BillingInfo.from_element(elem)

        return super(Account, self).__getattr__(name)

    def charge(self, charge):
        """Charge (or credit) this account with the given `Adjustment`."""
        url = urljoin(self._url, '%s/adjustments' % self.account_code)
        return charge.post(url)

    def invoice(self):
        """Create an invoice for any outstanding adjustments this account
            has."""
        url = urljoin(self._url, '%s/invoices' % self.account_code)

        response = self.http_request(url, 'POST')
        if response.status != 201:
            self.raise_http_error(response)

        response_xml = response.read()
        logging.getLogger('recurly.http.response').debug(response_xml)
        elem = ElementTree.fromstring(response_xml)

        invoice = Invoice.from_element(elem)
        invoice._url = response.getheader('Location')
        return invoice

    def reopen(self):
        """Reopen a closed account."""
        url = urljoin(self._url, '%s/reopen' % self.account_code)
        response = self.http_request(url, 'PUT')
        if response.status != 200:
            self.raise_http_error(response)

        response_xml = response.read()
        logging.getLogger('recurly.http.response').debug(response_xml)
        self.update_from_element(ElementTree.fromstring(response_xml))

    def subscribe(self, subscription):
        """Create the given `Subscription` for this existing account."""
        url = urljoin(self._url, '%s/subscriptions' % self.account_code)
        return subscription.post(url)

    def update_billing_info(self, billing_info):
        """Change this account's billing information to the given
           `BillingInfo`."""
        url = urljoin(self._url, '%s/billing_info' % self.account_code)
        response = billing_info.http_request(url, 'PUT', billing_info,
            {'Content-Type': 'application/xml; charset=utf-8'})
        if response.status == 200:
            pass
        elif response.status == 201:
            billing_info._url = response.getheader('Location')
        else:
            billing_info.raise_http_error(response)

        response_xml = response.read()
        logging.getLogger('recurly.http.response').debug(response_xml)
        billing_info.update_from_element(ElementTree.fromstring(response_xml))


class BillingInfo(Resource):

    """A set of billing information for an account."""

    nodename = 'billing_info'

    attributes = (
        'type',
        'first_name',
        'last_name',
        'number',
        'verification_value',
        'year',
        'month',
        'start_month',
        'start_year',
        'issue_number',
        'company',
        'address1',
        'address2',
        'city',
        'state',
        'zip',
        'country',
        'phone',
        'vat_number',
        'ip_address',
        'ip_address_country',
        'card_type',
        'first_six',
        'last_four',
        'billing_agreement_id',
    )
    sensitive_attributes = ('number', 'verification_value')
    xml_attribute_attributes = ('type',)
    linked_attributes = ('account',)
    js_attributes = (
        'first_name',
        'last_name',
        'company',
        'address1',
        'address2',
        'city',
        'state',
        'zip',
        'country',
        'phone',
        'vat_number',
    )


class Coupon(Resource):

    """A coupon for a customer to apply to their account."""

    member_path = 'coupons/%s'
    collection_path = 'coupons'

    nodename = 'coupon'

    attributes = (
        'coupon_code',
        'name',
        'discount_type',
        'discount_percent',
        'discount_in_cents',
        'redeem_by_date',
        'single_use',
        'applies_for_months',
        'max_redemptions',
        'applies_to_all_plans',
        'created_at',
        'plan_codes',
    )
    linked_attributes = ('redemptions',)

    @classmethod
    def value_for_element(cls, elem):
        if not elem or elem.tag != 'plan_codes' or \
                elem.attrib.get('type') != 'array':
            return super(Coupon, cls).value_for_element(elem)

        return [code_elem.text for code_elem in elem]

    @classmethod
    def element_for_value(cls, attrname, value):
        if attrname != 'plan_codes':
            return super(Coupon, cls).element_for_value(attrname, value)

        elem = ElementTree.Element(attrname)
        elem.attrib['type'] = 'array'
        for code in value:
            code_el = ElementTree.Element('plan_code')
            code_el.text = code
            elem.append(code_el)

        return elem

    @classmethod
    def all_redeemable(cls, **kwargs):
        """Return a `Page` of redeemable coupons.

        This is a convenience method for `Coupon.all(state='redeemable')`.

        """
        return cls.all(state='redeemable', **kwargs)

    @classmethod
    def all_expired(cls, **kwargs):
        """Return a `Page` of expired coupons.

        This is a convenience method for `Coupon.all(state='expired')`.

        """
        return cls.all(state='expired', **kwargs)

    @classmethod
    def all_maxed_out(cls, **kwargs):
        """Return a `Page` of coupons that have been used the maximum
        number of times.

        This is a convenience method for `Coupon.all(state='maxed_out')`.

        """
        return cls.all(state='maxed_out', **kwargs)


class Redemption(Resource):

    """A particular application of a coupon to a customer account."""

    nodename = 'redemption'

    attributes = (
        'account_code',
        'single_use',
        'total_discounted_in_cents',
        'currency',
        'created_at',
    )
    linked_attributes = ('account', 'coupon',)


class Adjustment(Resource):

    """A charge or credit applied (or to be applied) to an account's
       invoice."""

    nodename = 'adjustment'

    attributes = (
        'uuid',
        'description',
        'accounting_code',
        'quantity',
        'unit_amount_in_cents',
        'discount_in_cents',
        'tax_in_cents',
        'total_in_cents',
        'currency',
        'taxable',
        'start_date',
        'end_date',
        'created_at',
        'type',
    )
    xml_attribute_attributes = ('type',)
    linked_attributes = ('account',)


class Invoice(Resource):

    """A payable charge to an account for the customer's charges and
    subscriptions."""

    member_path = 'invoices/%s'
    collection_path = 'invoices'

    nodename = 'invoice'

    attributes = (
        'uuid',
        'state',
        'invoice_number',
        'po_number',
        'vat_number',
        'subtotal_in_cents',
        'tax_in_cents',
        'total_in_cents',
        'currency',
        'created_at',
        'line_items',
        'transactions',
    )
    linked_attributes = ('account',)

    def as_pdf(self, **kwargs):
        """Return the resource at the given URL, as a
        (`httplib.HTTPResponse`, `xml.etree.ElementTree.Element`) tuple
        resulting from a ``GET`` request to that URL."""
        cls = self.__class__
        url = urljoin(BASE_URI, self.member_path % (self.attributes['uuid'],))

        response = cls.http_request(url, headers={'Accept': 'application/pdf'})
        if response.status != 200:
            cls.raise_http_error(response)

        assert response.getheader('Content-Type').startswith('application/pdf')

        response_pdf = response.read()

        return response_pdf

    @classmethod
    def all_open(cls, **kwargs):
        """Return a `Page` of open invoices.

        This is a convenience method for `Invoice.all(state='open')`.

        """
        return cls.all(state='open', **kwargs)

    @classmethod
    def all_collected(cls, **kwargs):
        """Return a `Page` of collected invoices.

        This is a convenience method for `Invoice.all(state='collected')`.

        """
        return cls.all(state='collected', **kwargs)

    @classmethod
    def all_failed(cls, **kwargs):
        """Return a `Page` of failed invoices.

        This is a convenience method for `Invoice.all(state='failed')`.

        """
        return cls.all(state='failed', **kwargs)

    @classmethod
    def all_past_due(cls, **kwargs):
        """Return a `Page` of past-due invoices.

        This is a convenience method for `Invoice.all(state='past_due')`.

        """
        return cls.all(state='past_due', **kwargs)


class Subscription(Resource):

    """A customer account's subscription to your service."""

    member_path = 'subscriptions/%s'
    collection_path = 'subscriptions'

    nodename = 'subscription'

    attributes = (
        'uuid',
        'state',
        'plan_code',
        'coupon_code',
        'quantity',
        'activated_at',
        'canceled_at',
        'starts_at',
        'expires_at',
        'current_period_started_at',
        'current_period_ends_at',
        'trial_started_at',
        'trial_ends_at',
        'unit_amount_in_cents',
        'total_billing_cycles',
        'first_renewal_date',
        'timeframe',
        'currency',
        'pending_subscription',
        'subscription_add_ons',

        # TODO: (IW) This should be a linked_attribute, but it breaks
        # Django-Recurly unless it's here - figure out why and fix it.
        'account',
    )
    sensitive_attributes = ('number', 'verification_value',)
    linked_attributes = ('account',)
    js_attributes = (
        'plan_code',
        'coupon_code',
        'quantity',
        'starts_at',
        'trial_ends_at',
        'unit_amount_in_cents',
        'total_billing_cycles',
        'first_renewal_date',
    )

    def _update(self):
        if not hasattr(self, 'timeframe'):
            self.timeframe = 'now'
        return super(Subscription, self)._update()

    def __getpath__(self, name):
        if name == 'plan_code':
            return 'plan/plan_code'
        else:
            return name

    @classmethod
    def all_live(cls, **kwargs):
        """Return a `Page` of subscriptions that are not expired.

        This is a convenience method for `Subscription.all(state='live')`.

        """
        return cls.all(state='live', **kwargs)

    @classmethod
    def all_active(cls, **kwargs):
        """Return a `Page` of subscriptions that are valid for the current time. This includes subscriptions in a trial period.

        This is a convenience method for `Subscription.all(state='active')`.

        """
        return cls.all(state='active', **kwargs)

    @classmethod
    def all_canceled(cls, **kwargs):
        """Return a `Page` of subscriptions that are valid for the current time but will not renew because a cancelation was requested.

        This is a convenience method for `Subscription.all(state='canceled')`.

        """
        return cls.all(state='canceled', **kwargs)

    @classmethod
    def all_expired(cls, **kwargs):
        """Return a `Page` of subscriptions that have expired and are no longer valid.

        This is a convenience method for `Subscription.all(state='expired')`.

        """
        return cls.all(state='expired', **kwargs)

    @classmethod
    def all_future(cls, **kwargs):
        """Return a `Page` of subscriptions that will start in the future, they are not active yet.

        This is a convenience method for `Subscription.all(state='future')`.

        """
        return cls.all(state='future', **kwargs)

    @classmethod
    def all_trial(cls, **kwargs):
        """Return a `Page` of subscriptions that are active or canceled and are in a trial period.

        This is a convenience method for `Subscription.all(state='in_trial')`.

        """
        return cls.all(state='in_trial', **kwargs)

    @classmethod
    def all_past_due(cls, **kwargs):
        """Return a `Page` of subscriptions that are active or canceled and have a past-due invoice.

        This is a convenience method for `Subscription.all(state='past_due')`.

        """
        return cls.all(state='past_due', **kwargs)


class Transaction(Resource):

    """An immediate one-time charge made to a customer's account."""

    member_path = 'transactions/%s'
    collection_path = 'transactions'

    nodename = 'transaction'

    attributes = (
        'uuid',
        'action',
        'currency',
        'amount_in_cents',
        'tax_in_cents',
        'status',
        'source',
        'reference',
        'test',
        'voidable',
        'description',
        'refundable',
        'cvv_result',
        'avs_result',
        'avs_result_street',
        'avs_result_postal',
        'created_at',
        'details',
        'transaction_error',
        'type',

        # TODO: (IW) This should be a linked_attribute, but it breaks
        # Django-Recurly unless it's here - figure out why and fix it.
        'account',
    )
    xml_attribute_attributes = ('type',)
    sensitive_attributes = ('number', 'verification_value',)
    linked_attributes = ('account', 'invoice', 'subscription')
    js_attributes = (
        'currency',
        'amount_in_cents',
        # 'dscription',
        # 'accounting_code',
    )

    def _handle_refund_accepted(self, response):
        if response.status != 202:
            self.raise_http_error(response)

        self._refund_transaction_url = response.getheader('Location')
        return self

    def get_refund_transaction(self):
        """Retrieve the refund transaction for this transaction, immediately
        after refunding.

        After calling `refund()` to refund a transaction, call this method to
        retrieve the new transaction representing the refund.

        """
        try:
            url = self._refund_transaction_url
        except AttributeError:
            raise ValueError("No refund transaction is available for this transaction")  # noqa

        resp, elem = self.element_for_url(url)
        value = self.value_for_element(elem)
        return value

    def refund(self, **kwargs):
        """Refund this transaction.

        Calling this method returns the refunded transaction (that is,
        ``self``) if the refund was successful, or raises a `ResponseError` if
        an error occurred requesting the refund. After a successful call to
        `refund()`, to retrieve the new transaction representing the refund,
        use the `get_refund_transaction()` method.

        """
        # Find the URL and method to refund the transaction.
        try:
            selfnode = self._elem
        except AttributeError:
            raise AttributeError('refund')
        url, method = None, None
        for anchor_elem in selfnode.findall('a'):
            if anchor_elem.attrib.get('name') == 'refund':
                url = anchor_elem.attrib['href']
                method = anchor_elem.attrib['method'].upper()
        if url is None or method is None:
            # should do something more specific probably
            raise AttributeError("refund")

        actionator = self._make_actionator(
            url, method, extra_handler=self._handle_refund_accepted)
        return actionator(**kwargs)


class Details(Resource):

    """Additional transaction information recorded at the time the transaction
    was submitted.

    This will include the account and billing information as it was at the time
    the transaction took place. It may not reflect the latest account
    information. A `transaction_error` section will be included if the
    transaction failed.

    """

    nodename = 'details'
    inherits_currency = False

    attributes = (
        'account',
        'transaction_error'
    )


class TransactionError(Resource):

    """When Recurly encounters an error submitting a payment to your gateway,
    it parses the error code. From your gateway's error code, Recurly generates
    a friendly error message that can be displayed to your user and returns it
    in the error object. In addition, Recurly sets a code on the error to let
    you know exactly why the transaction was declined.

    """

    nodename = 'transaction_error'
    inherits_currency = False

    attributes = (
        'error_code',
        'error_category',
        'merchant_message',
        'customer_message',
    )


class Plan(Resource):

    """A service level for your service to which a customer account
    can subscribe."""

    member_path = 'plans/%s'
    collection_path = 'plans'

    nodename = 'plan'

    attributes = (
        'plan_code',
        'name',
        'description',
        'success_url',
        'cancel_url',
        'display_donation_amounts',
        'display_quantity',
        'display_phone_number',
        'bypass_hosted_confirmation',
        'unit_name',
        'payment_page_tos_link',
        'plan_interval_length',
        'plan_interval_unit',
        'trial_interval_length',
        'trial_interval_unit',
        'accounting_code',
        'created_at',
        'unit_amount_in_cents',
        'setup_fee_in_cents',
    )
    linked_attributes = ('add_ons',)
    js_attributes = (
        'plan_code',
        'name',
        'description',
        'success_url',
        'cancel_url',
        'display_donation_amounts',
        'display_quantity',
        'display_phone_number',
        'bypass_hosted_confirmation',
        'unit_name',
        'payment_page_tos_link',
        'plan_interval_length',
        'plan_interval_unit',
        'trial_interval_length',
        'trial_interval_unit',
        'accounting_code',
        'created_at',
        'unit_amount_in_cents',
        'setup_fee_in_cents',
    )

    def get_add_on(self, add_on_code):
        """Return the `AddOn` for this plan with the given add-on code."""
        url = urljoin(self._url, '%s/add_ons/%s' %
            (self.plan_code, add_on_code))
        resp, elem = AddOn.element_for_url(url)
        return AddOn.from_element(elem)

    def create_add_on(self, add_on):
        """Make the given `AddOn` available to subscribers on this plan."""
        url = urljoin(self._url, '%s/add_ons' % self.plan_code)
        return add_on.post(url)


class AddOn(Resource):

    """An additional benefit a customer subscribed to a particular plan
    can also subscribe to."""

    nodename = 'add_on'

    attributes = (
        'add_on_code',
        'name',
        'display_quantity_on_hosted_page',
        'display_quantity',
        'default_quantity',
        'accounting_code',
        'unit_amount_in_cents',
        'created_at',
    )
    linked_attributes = ('plan',)


class SubscriptionAddOn(Resource):

    """A plan add-on as added to a customer's subscription.

    Use these instead of `AddOn` instances when specifying a
    `Subscription` instance's `subscription_add_ons` attribute.

    """

    nodename = 'subscription_add_on'
    inherits_currency = True

    attributes = (
        'add_on_code',
        'quantity',
        'unit_amount_in_cents',
    )


Resource._learn_nodenames(locals().values())


def objects_for_push_notification(notification):
    """Decode a push notification with the given body XML.

    Returns a dictionary containing the constituent objects of the push
    notification. The kind of push notification is given in the ``"type"``
    member of the returned dictionary.

    NOTE: Push notification object attributes do not match up one-to-one with
    their Recurly Resource counterparts. Some attributes will be trimmed in this
    process.
    """
    notification_el = ElementTree.fromstring(notification)
    objects = {'type': notification_el.tag}
    for child_el in notification_el:
        tag = child_el.tag
        res = Resource.value_for_element(child_el)
        objects[tag] = res
    return objects
