---
config:
  theme: dark
---
erDiagram
    EMPLOYEE ||--o{ GUEST_CHECK : opens
    EMPLOYEE ||--o{ LINE_ITEM   : records
    STORE    ||--o{ GUEST_CHECK : has
    STORE    ||--o{ EMPLOYEE    : employs
    GUEST_CHECK ||--|{ GUEST_CHECK_TAX : includes
    GUEST_CHECK ||--|{ LINE_ITEM       : contains
    LINE_ITEM ||--|| LINE_ITEM_MENU     : details
    LINE_ITEM ||--|| LINE_ITEM_DISCOUNT : discounts
    LINE_ITEM ||--|| LINE_ITEM_PAYMENT  : payments
    STORE {
        string store_id PK
        string name
    }
    EMPLOYEE {
        int    employee_id PK
        string store_id FK
        int    employee_number
    }
    GUEST_CHECK {
        int       guest_check_id PK
        string    store_id FK
        int       employee_id FK
        string    table_name
        int       table_number
        int       check_number
        int       revenue_center_number
        int       order_type_number
        int       service_rounds
        int       check_printeds
        numeric   sub_total
        numeric   discount_total
        numeric   check_total
        numeric   non_taxable_sales_total
        timestamp opened_utc
        timestamp closed_utc
        timestamp last_updated_utc
        timestamp last_transaction_utc
        boolean   closed_flag
    }
    GUEST_CHECK_TAX {
        int     guest_check_id PK
        int     tax_number     PK
        numeric taxable_sales
        numeric tax_collected
        numeric tax_rate
    }
    LINE_ITEM {
        int       line_item_id PK
        int       guest_check_id FK
        int       employee_id FK
        int       line_number
        string    item_type
        int       revenue_center_number
        int       order_type_number
        int       workstation_number
        timestamp detail_utc
        numeric   display_total
        numeric   display_quantity
        numeric   aggregation_total
        numeric   aggregation_quantity
    }
    LINE_ITEM_MENU {
        int     line_item_id PK
        int     menu_item_number
        boolean modified_flag
        numeric incl_tax
        string  active_taxes
        int     price_level
    }
    LINE_ITEM_DISCOUNT {
        int     line_item_id PK
        numeric discount_amount
        string  discount_reason
    }
    LINE_ITEM_PAYMENT {
        int     line_item_id PK
        string  tender_type
        numeric paid_amount
    }
