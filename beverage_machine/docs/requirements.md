# Automatic Water Dispenser System

## 1. Project Overview

The Automatic Water Dispenser is a self-service water vending system for customers in Nepal. Customers can select a container, choose water temperature and volume, pay through an approved eSewa payment flow, and receive the measured quantity of water.

## 2. Project Objectives

- Provide self-service water dispensing.
- Support customers bringing their own bottles.
- Support machine-dispensed disposable cups.
- Offer cold, normal and hot water options.
- Support volume selection: 250 mL, 500 mL, 1 L and 2 L.
- Integrate an approved eSewa merchant payment flow.
- Verify payments securely on the backend.
- Measure and record the actual dispensed volume.
- Monitor machine status and important sensor readings.

## 3. User Roles

### Customer
- Scan the machine QR code.
- Select a container type.
- Select water temperature.
- Choose the desired volume.
- View the total price.
- Complete payment.
- View payment and dispensing status.

### Administrator
- Manage machine information.
- Manage water options and prices.
- Manage cup inventory.
- View orders and payment records.
- Monitor machine status and faults.
- Review dispensing history and reports.

## 4. Proposed Technology Stack

- Backend: Python and Django REST Framework
- Database: PostgreSQL
- Initial customer interface: Mobile-friendly web application
- Payment: Approved eSewa merchant integration
- Machine controller: ESP32
- Documentation: Markdown files in VS Code
- Version control: Git and GitHub

## 5. Main Functional Requirements

### FR-01: Machine Identification
The system shall identify the machine associated with a customer order.

### FR-02: Container Selection
The customer shall be able to select their own bottle or request a disposable cup.

### FR-03: Water Selection
The customer shall be able to select cold, normal or hot water, subject to machine availability.

### FR-04: Volume Selection
The customer shall be able to select 250 mL, 500 mL, 1 L or 2 L.

### FR-05: Price Calculation
The backend shall calculate the total price using the configured water price and applicable container fee.

### FR-06: Payment Verification
The backend shall verify the payment through the approved payment-provider flow before authorizing dispensing.

### FR-07: Dispensing
The machine shall dispense the authorized quantity and report the measured volume.

### FR-08: Cup Dispensing
When a disposable cup is selected, the machine shall release a cup and verify its presence before filling.

### FR-09: Order History
The system shall record order, payment and dispensing statuses.

### FR-10: Safety and Fault Handling
The system shall handle low water, leakage, temperature faults, sensor errors, network failures and dispensing timeouts safely.

## 6. Non-Functional Requirements

- Protect payment credentials and customer data.
- Prevent duplicate payment authorization and duplicate dispensing.
- Keep reliable order and machine logs.
- Validate API requests and handle errors clearly.
- Provide a usable mobile interface.
- Maintain secure communication between the backend and machine controller.

## 7. Initial Development Scope

- Build and test the backend locally.
- Simulate payment and machine responses first.
- Implement order and payment records.
- Test the dispensing workflow without real money.
- Integrate hardware and the approved payment provider in later phases.

## 8. Project Limitations

- Real payment integration requires merchant approval and provider-supported documentation.
- Actual hardware behaviour must be verified on the physical machine.
- Water treatment, food safety, electrical safety and applicable local requirements must be validated before commercial deployment.

## 9. Future Enhancements

- Machine monitoring dashboard.
- Automated maintenance alerts.
- Sales and usage reports.
- Multiple-machine management.
- Additional payment options if approved.

## 10. Document Status

Version: 1.1  
Status: Updated initial requirements draft  
Next review: After database design and workflow validation.