# Database Design

## 1. Purpose

The database stores information about machines, water options, containers, inventory, orders, payments, dispensing jobs and machine telemetry.

## 2. Proposed Entities

### 2.1 Machine
- id
- machine_code
- location
- status
- last_seen_at

### 2.2 WaterOption
- id
- name
- temperature_type
- is_available

### 2.3 ContainerType
- id
- name
- container_fee_paisa
- is_available

Container types initially include:
- Own bottle
- Disposable cup

### 2.4 Inventory
- id
- machine
- container_type
- quantity_available
- updated_at

### 2.5 Order
- id
- machine
- water_option
- container_type
- volume_ml
- water_amount_paisa
- container_fee_paisa
- total_amount_paisa
- status
- created_at

### 2.6 Payment
- id
- order
- provider
- transaction_reference
- amount_paisa
- status
- verified_at

### 2.7 DispenseJob
- id
- order
- command_id
- target_volume_ml
- actual_volume_ml
- status
- started_at
- completed_at

### 2.8 MachineTelemetry
- id
- machine
- tank_level
- cold_temperature
- hot_temperature
- leak_detected
- recorded_at

## 3. Relationships

- One machine can receive many orders.
- One water option can be selected in many orders.
- One container type can be used in many orders.
- One machine can have inventory records for different container types.
- An order can have payment records.
- An order can have dispensing jobs.
- One machine can produce many telemetry records.

## 4. Data Rules

- Monetary values are stored as integer paisa.
- Volume is stored in millilitres.
- Prices are calculated by the backend.
- Payment status and dispensing status are separate.
- Each dispensing command has a unique identifier.
- Inventory changes must be recorded consistently.
- The system must not dispense without verified payment.
- Failed dispensing must be recorded for reconciliation.

## 5. Design Notes

This is an initial logical design. Field types, constraints, indexes, deletion rules and final relationships will be confirmed before implementation.

## 6. Document Status

Version: 1.1  
Status: Initial database design draft.
## 7. Relationship Explanation

### One-to-Many Relationships

- Machine to Order: One machine can receive multiple orders.
- Order to Payment: One order may have multiple payment records, for example when payment attempts need to be recorded.
- Order to DispenseJob: One order may have multiple dispensing job records for retries or recovery.
- Machine to Inventory: One machine can store multiple container inventory records.
- Machine to MachineTelemetry: One machine can produce multiple sensor readings over time.

### Foreign Keys

Foreign keys connect related records across tables. For example, Order.machine references Machine.id, and Payment.order references Order.id.

### Integrity Rules

- An order must reference a valid machine.
- Payment records must reference a valid order.
- Dispensing records must reference a valid order.
- Repeated payment notifications must not authorize duplicate dispensing.

## 8. Review Status

The relationships are proposed for the initial implementation. Final database constraints will be confirmed during Django model development.