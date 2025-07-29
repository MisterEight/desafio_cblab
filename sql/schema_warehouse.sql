-- schema_warehouse.sql  –  Coco Bambu 2025
-- Emgloba o locRef no JSON, apenas o básico para fazer conexão com a tabela de guest_check.
CREATE TABLE store (
    store_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Emgloba o empNum no JSON, apenas o básico para fazer conexão com a tabela de guest_check.
CREATE TABLE employee (
    employee_id BIGINT PRIMARY KEY,
    store_id VARCHAR(20) NOT NULL REFERENCES store(store_id),
    employee_number INT NOT NULL UNIQUE 
    -- Se o número do funcionário está no check provável que seja único para achar o funcionário.
);

-- Emgloba o cabeçalho que está no guestChecks no JSON
CREATE TABLE guest_check (
    guest_check_id BIGINT PRIMARY KEY,
    store_id VARCHAR(20) NOT NULL REFERENCES store(store_id),
    employee_number BIGINT NOT NULL,
    -- No cabeçalho do guest_check não possuí o employee_id, apenas o number
    table_name VARCHAR(30),
    -- Pode ser aumentado caso o padrão seja maior.
    table_number SMALLINT,
    -- Assumo que seja um número pequeno. Ex: 01, 03, 50.
    check_number INT,
    -- Pode ser trasnformado em SMALLINT caso o número não seja tão grande.
    revenue_center_number SMALLINT,
    order_type_number SMALLINT,
    -- Pode virar um ENUM para melhorar a categorização do dado
    service_rounds SMALLINT,
    check_printeds SMALLINT,
    guest_count SMALLINT,
    sub_total NUMERIC(12, 2),
    discount_total NUMERIC(12, 2),
    check_total NUMERIC(12, 2),
    non_taxable_sales_total NUMERIC(12, 2),
    opened_utc TIMESTAMP WITH TIME ZONE,
    closed_utc TIMESTAMP WITH TIME ZONE,
    last_updated_utc TIMESTAMP WITH TIME ZONE,
    last_transaction_utc TIMESTAMP WITH TIME ZONE,
    closed_flag BOOLEAN DEFAULT FALSE -- Default com FalsE, o check é aberto e precisa ser fechado.
);

-- Emgloba as informações que estão no taxes dentro do JSON
CREATE TABLE guest_check_tax (
    guest_check_id BIGINT NOT NULL REFERENCES guest_check(guest_check_id),
    tax_number SMALLINT NOT NULL,
    taxable_sales NUMERIC(12, 2),
    tax_collected NUMERIC(12, 2),
    tax_rate NUMERIC(8, 6),
    PRIMARY KEY (guest_check_id, tax_number) -- Chave composta, um pédido pode ter vários tipos de taxa e evitar taxas duplicadas.
);

-- Emgloba as informações que estão no detailLines dentro do JSON
CREATE TABLE line_item (
    line_item_id BIGINT PRIMARY KEY,
    guest_check_id BIGINT NOT NULL REFERENCES guest_check(guest_check_id),
    employee_id BIGINT NOT NULL REFERENCES employee(employee_id),
    line_number SMALLINT,
    revenue_center_number SMALLINT,
    order_type_number SMALLINT,
    workstation_number SMALLINT,
    detail_utc TIMESTAMP WITH TIME ZONE,
    display_total NUMERIC(12, 2),
    display_quantity SMALLINT,
    aggregation_total NUMERIC(12, 2),
    aggregation_quantity SMALLINT
);

-- Emgloba as informações que estão no menuItem dentro do JSON
CREATE TABLE line_item_menu (
    line_item_id BIGINT PRIMARY KEY REFERENCES line_item(line_item_id),
    menu_item_number INT,
    modified_flag BOOLEAN,
    incl_tax NUMERIC(12, 6),
    active_taxes VARCHAR(50),
    price_level SMALLINT
);

-- Emgloba os possíveis descontos que podem ter nos itens
CREATE TABLE line_item_discount (
    line_item_id BIGINT PRIMARY KEY REFERENCES line_item(line_item_id),
    discount_amount NUMERIC(12, 2),
    discount_reason VARCHAR(100)
);

-- Emgloba os possíveis tipos pagamentos e as quantidades que podem ter nos itens
CREATE TABLE line_item_payment (
    line_item_id BIGINT PRIMARY KEY REFERENCES line_item(line_item_id),
    tender_type VARCHAR(30),
    paid_amount NUMERIC(12, 2)
);

INSERT INTO
    store (store_id, name)
VALUES
    ('99 CB CB', 'Loja 99 Coco Bambu');

INSERT INTO
    employee (employee_id, store_id, employee_number)
VALUES
    (10324319, '99 CB CB', 55555);

INSERT INTO
    employee (employee_id, store_id, employee_number)
VALUES
    (10454318, '99 CB CB', 81001);

-- Indíces úteis.
CREATE INDEX idx_guest_check_store_date ON guest_check (store_id, opened_utc);

CREATE INDEX idx_line_item_guest_check ON line_item (guest_check_id);

CREATE INDEX idx_payment_tender ON line_item_payment (tender_type);