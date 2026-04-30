from datetime import datetime

from pydantic import BaseModel


class OrderParameter(BaseModel):
    Key: str | None = None
    Value: str | None = None
    DataType: str | int | None = None


class OrderTypeInfo(BaseModel):
    Id: int | None = None
    Name: str | None = None
    ShopOwnerId: int | None = None
    Active: bool | None = None
    FulfilmentPriority: int | None = None
    OrderTypeEnumValue: str | int | None = None


class OrderStatus(BaseModel):
    Comment: str | None = None
    ActionDate: datetime | None = None
    Id: int | None = None
    BaseOrderStatusId: int | None = None
    OrderStatusTypeId: int | None = None
    Name: str | None = None
    Enabled: bool | None = None


class ContactInfo(BaseModel):
    VatNumber: str | None = None
    FullName: str | None = None
    DateOfBirth: datetime | None = None
    Gender: str | None = None
    PersonTitle: str | None = None
    MiddleName: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    LastNamePrefix: str | None = None
    Id: int | None = None
    CompanyName: str | None = None
    Address: str | None = None
    Address2: str | None = None
    StreetAddress: str | None = None
    StreetAddressNumber: str | None = None
    StreetAddressExtension: str | None = None
    PostalCode: str | None = None
    City: str | None = None
    CountryId: int | None = None
    CountryCode: str | None = None
    CountryName: str | None = None
    EMail: str | None = None
    Phone: str | None = None
    Phone2: str | None = None
    StateProvince: str | None = None
    StateProvinceCode: str | None = None


class OrderRowParameter(BaseModel):
    Key: str | None = None
    Value: str | None = None
    DataType: str | int | None = None


class OrderRow(BaseModel):
    Id: int | None = None
    ProductSelectionProductId: int | None = None
    ProductId: int | None = None
    OrderRowKey: str | None = None
    ItemQuantity: float | None = None
    ProductName: str | None = None
    ProductCode: str | None = None
    ProductDescription: str | None = None
    ItemPriceExVat: float | None = None
    ItemPriceIncVat: float | None = None
    ItemDiscountExVat: float | None = None
    ItemDiscountIncVat: float | None = None
    RowDiscountExVat: float | None = None
    RowDiscountIncVat: float | None = None
    Vatperc: float | None = None
    VATTariffId: int | None = None
    VATTariffCode: str | None = None
    RowTotalExVat: float | None = None
    RowTotalIncVat: float | None = None
    Comment: str | None = None
    SupplierId: int | None = None
    ItemPurchasePrice: float | None = None
    CreditForOrderRowId: int | None = None
    Sequence: int | None = None
    ShopProductUrl: str | None = None
    ShopProductImageUrl: str | None = None
    ShipmentId: int | None = None
    StockStatus: str | int | None = None
    IsAllocated: bool | None = None
    WarehouseId: int | None = None
    WarehouseSelectionMethod: str | int | None = None
    Params: list[OrderRowParameter] = []
    DisableRecalculate: bool | None = None


class ParcelBasicInfo(BaseModel):
    Id: int | None = None
    TrackingCode: str | None = None
    TrackingUrl: str | None = None
    CreateTimestamp: datetime | None = None
    ChangedTimestamp: datetime | None = None
    CarrierName: str | None = None
    ShopId: int | None = None
    OrderId: int | None = None


class ShipmentBasicInfo(BaseModel):
    Id: int | None = None
    ShippingCode: str | None = None
    CreateTimestamp: datetime | None = None
    ChangeTimestamp: datetime | None = None
    ShopId: int | None = None
    OrderId: int | None = None
    OrderCode: str | None = None
    WarehouseId: int | None = None
    ParcelId: int | None = None
    PickedTimestamp: datetime | None = None
    PackedTimestamp: datetime | None = None
    ShippedTimestamp: datetime | None = None
    HandOverTimestamp: datetime | None = None
    ShipmentType: str | None = None


class OrderBasicInfo(BaseModel):
    CompanyName: str | None = None
    FullName: str | None = None
    Id: int
    OrderCode: str | None = None
    Type: str | int | None = None
    OrderTypeId: int | None = None
    Date: datetime | None = None
    OrderTotalIncVat: float | None = None
    OrderTotalExVat: float | None = None
    CurrencyId: int | None = None
    CurrencyCode: str | None = None
    Deleted: bool | None = None
    ChangeTimestamp: datetime | None = None
    MainStatusId: int | None = None
    AffiliateId: int | None = None


class Order(BaseModel):
    OrderType: OrderTypeInfo | None = None
    PreferredDeliveryDate: datetime | None = None
    MainStatus: OrderStatus | None = None
    PaymentStatus: OrderStatus | None = None
    StockStatus: OrderStatus | None = None
    FulfilmentStatus: OrderStatus | None = None
    ShipmentStatus: OrderStatus | None = None
    CustomStatus: OrderStatus | None = None
    CultureCode: str | None = None
    CultureId: int | None = None
    Incoterms: str | None = None
    ExchangeRate: float | None = None
    ShopId: int | None = None
    ViewModusIncVAT: bool | None = None
    ExternalOrderKey: str | None = None
    CouponCode: str | None = None
    PaymentFeeIncVat: float | None = None
    PaymentFeeExVat: float | None = None
    ShippingCostsIncVat: float | None = None
    ShippingCostsExVat: float | None = None
    PaymentTypeId: int | None = None
    PurchaseTypeId: int | None = None
    CarrierAccountId: int | None = None
    CustomerId: int | None = None
    CustomerCode: str | None = None
    CustomerReference: str | None = None
    CustomerNote: str | None = None
    CustomerRating: str | int | None = None
    ShopNote: str | None = None
    SyncSource: str | None = None
    CustomerIpaddress: str | None = None
    DiscountExVat: float | None = None
    DiscountIncVat: float | None = None
    BillToContact: ContactInfo | None = None
    ShipToContact: ContactInfo | None = None
    Params: list[OrderParameter] = []
    OrderRows: list[OrderRow] = []
    Parcels: list[ParcelBasicInfo] = []
    Shipments: list[ShipmentBasicInfo] = []
    Id: int
    OrderCode: str | None = None
    Type: str | int | None = None
    OrderTypeId: int | None = None
    Date: datetime | None = None
    OrderTotalIncVat: float | None = None
    OrderTotalExVat: float | None = None
    CurrencyId: int | None = None
    CurrencyCode: str | None = None
    Deleted: bool | None = None
    ChangeTimestamp: datetime | None = None
    MainStatusId: int | None = None
    AffiliateId: int | None = None

