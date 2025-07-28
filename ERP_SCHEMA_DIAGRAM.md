# ERP System Database Schema Diagram

This document contains the complete Entity Relationship Diagram (ERD) for the ERP System database schema, organized by modules.

## Complete ERP Schema Overview

```mermaid
erDiagram
    %% ==========================================
    %% USER AUTHENTICATION & COMPANY MODULE
    %% ==========================================
    
    user_auth_company {
        bigint id PK
        varchar name UK
        text address
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    user_auth_role {
        bigint id PK
        varchar name UK
        text description
        varchar department
        int level
        boolean is_active
        bigint parent_id FK
    }
    
    user_auth_user {
        bigint id PK
        varchar password
        timestamp last_login
        boolean is_superuser
        varchar email UK
        varchar first_name
        varchar last_name
        boolean is_active
        boolean is_staff
        timestamp date_joined
        bigint company_id FK
        bigint role_id FK
    }
    
    user_auth_user_groups {
        bigint id PK
        bigint user_id FK
        int group_id FK
    }
    
    user_auth_user_user_permissions {
        bigint id PK
        bigint user_id FK
        int permission_id FK
    }
    
    user_auth_activitylog {
        bigint id PK
        varchar action
        text details
        inet ip_address
        timestamp created_at
        bigint user_id FK
    }
    
    %% ==========================================
    %% ACCOUNTING MODULE
    %% ==========================================
    
    accounting_accountcategory {
        bigint id PK
        varchar code
        varchar name
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
    }
    
    accounting_accountgroup {
        bigint id PK
        varchar code
        varchar name
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint category_id FK
    }
    
    accounting_account {
        bigint id PK
        varchar code UK
        varchar name
        text description
        varchar account_type
        boolean is_group
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint group_id FK
        bigint parent_id FK
    }
    
    accounting_journalentry {
        bigint id PK
        varchar journal_number UK
        date entry_date
        text description
        varchar reference
        numeric total_debit
        numeric total_credit
        varchar status
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
    }
    
    accounting_journalentryline {
        bigint id PK
        text description
        numeric debit_amount
        numeric credit_amount
        timestamp created_at
        bigint account_id FK
        bigint journal_entry_id FK
    }
    
    %% ==========================================
    %% CRM MODULE
    %% ==========================================
    
    crm_partner {
        bigint id PK
        varchar name
        varchar partner_type
        varchar email
        varchar phone
        text address
        varchar tax_number
        boolean is_customer
        boolean is_supplier
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
    }
    
    crm_customer {
        bigint id PK
        varchar name
        varchar email
        varchar phone
        text address
        varchar payment_terms
        numeric credit_limit
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint partner_id FK
    }
    
    %% ==========================================
    %% PRODUCTS MODULE
    %% ==========================================
    
    products_productcategory {
        bigint id PK
        varchar name
        varchar code
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint parent_id FK
    }
    
    products_attribute {
        bigint id PK
        varchar name
        varchar data_type
        boolean is_required
        boolean is_active
        timestamp created_at
        bigint company_id FK
    }
    
    products_attributevalue {
        bigint id PK
        varchar value
        boolean is_active
        timestamp created_at
        bigint attribute_id FK
    }
    
    products_product {
        bigint id PK
        varchar name
        varchar sku UK
        varchar barcode
        text description
        varchar product_type
        varchar unit_of_measure
        numeric weight
        varchar dimensions
        numeric cost_price
        numeric selling_price
        boolean is_active
        boolean is_saleable
        boolean is_purchasable
        boolean is_manufacturable
        boolean is_stockable
        numeric minimum_stock
        numeric maximum_stock
        numeric reorder_level
        text notes
        varchar image
        boolean is_variant
        varchar tracking_method
        boolean requires_batch_tracking
        boolean requires_expiry_tracking
        boolean requires_individual_tracking
        int shelf_life_days
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint updated_by_id FK
        bigint category_id FK
        bigint default_variant_id FK
    }
    
    products_productvariant {
        bigint id PK
        varchar name
        varchar sku UK
        varchar color
        varchar size
        varchar material
        numeric cost_price
        numeric selling_price
        numeric minimum_stock
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint product_id FK
    }
    
    products_productattribute {
        bigint id PK
        varchar value
        timestamp created_at
        bigint attribute_id FK
        bigint product_id FK
    }
    
    products_producttracking {
        bigint id PK
        varchar serial_number UK
        varchar imei_number UK
        varchar barcode
        varchar batch_number
        date purchase_date
        date manufacturing_date
        date expiry_date
        date warranty_expiry
        numeric purchase_price
        varchar status
        varchar quality_status
        varchar location_notes
        varchar supplier_batch_reference
        text service_history
        text notes
        jsonb custom_fields
        timestamp created_at
        timestamp updated_at
        bigint created_by_id FK
        bigint product_id FK
        bigint variant_id FK
        bigint current_warehouse_id FK
        bigint grn_item_id FK
        bigint supplier_id FK
    }
    
    %% ==========================================
    %% INVENTORY MODULE
    %% ==========================================
    
    inventory_warehouse {
        bigint id PK
        varchar name
        varchar code
        text address
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint manager_id FK
    }
    
    inventory_stockitem {
        bigint id PK
        numeric quantity_on_hand
        numeric quantity_reserved
        numeric quantity_available
        numeric average_cost
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
        bigint product_id FK
        bigint warehouse_id FK
    }
    
    inventory_stockmovement {
        bigint id PK
        varchar movement_type
        numeric quantity
        varchar reference_type
        bigint reference_id
        text notes
        timestamp movement_date
        timestamp created_at
        bigint created_by_id FK
        bigint product_id FK
        bigint warehouse_id FK
    }
    
    inventory_stocklot {
        bigint id PK
        varchar lot_number UK
        date expiry_date
        numeric quantity
        varchar status
        timestamp created_at
        timestamp updated_at
        bigint product_id FK
        bigint warehouse_id FK
    }
    
    inventory_stockreservation {
        bigint id PK
        numeric quantity
        varchar status
        varchar reference_type
        bigint reference_id
        timestamp reserved_at
        timestamp expires_at
        timestamp created_at
        bigint created_by_id FK
        bigint product_id FK
        bigint warehouse_id FK
    }
    
    %% ==========================================
    %% PURCHASE MODULE
    %% ==========================================
    
    purchase_unitofmeasure {
        bigint id PK
        varchar name
        varchar abbreviation
        varchar uom_type
        boolean is_base_unit
        numeric conversion_factor
        boolean is_active
        timestamp created_at
        bigint company_id FK
    }
    
    purchase_supplier {
        bigint id PK
        varchar supplier_code UK
        varchar name
        varchar email
        varchar phone
        text address
        varchar contact_person
        varchar tax_number
        text bank_details
        varchar payment_terms
        numeric credit_limit
        int delivery_lead_time
        numeric quality_rating
        numeric delivery_rating
        boolean is_active
        varchar agreement_contract
        varchar bank_documents
        varchar quality_certificates
        varchar registration_certificate
        varchar tax_certificate
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint partner_id FK
    }
    
    purchase_purchaserequisition {
        bigint id PK
        varchar pr_number UK
        varchar department
        date request_date
        date required_date
        text purpose
        varchar status
        timestamp approved_at
        text rejected_reason
        numeric total_estimated_cost
        varchar budget_approval
        varchar requisition_document
        varchar technical_specifications
        timestamp created_at
        timestamp updated_at
        bigint approved_by_id FK
        bigint company_id FK
        bigint requested_by_id FK
        bigint warehouse_id FK
    }
    
    purchase_purchaserequisitionitem {
        bigint id PK
        numeric quantity
        numeric unit_price
        numeric total_amount
        text specifications
        numeric ordered_quantity
        bigint product_id FK
        bigint purchase_requisition_id FK
        bigint preferred_supplier_id FK
    }
    
    purchase_requestforquotation {
        bigint id PK
        varchar rfq_number UK
        date issue_date
        date response_deadline
        text terms_and_conditions
        varchar payment_terms
        varchar delivery_terms
        text description
        varchar status
        varchar drawing_attachments
        varchar rfq_document
        varchar technical_specifications
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint purchase_requisition_id FK
        bigint warehouse_id FK
    }
    
    purchase_requestforquotation_suppliers {
        bigint id PK
        bigint requestforquotation_id FK
        bigint supplier_id FK
    }
    
    purchase_rfqitem {
        bigint id PK
        numeric quantity
        text specifications
        numeric minimum_qty_required
        numeric maximum_qty_acceptable
        numeric target_unit_price
        varchar priority
        bigint product_id FK
        bigint rfq_id FK
        bigint required_uom_id FK
    }
    
    purchase_supplierquotation {
        bigint id PK
        varchar quotation_number
        date quotation_date
        date valid_until
        varchar payment_terms
        varchar delivery_terms
        int delivery_time_days
        numeric total_amount
        numeric discount_percentage
        numeric discount_amount
        varchar discount_type
        varchar discount_application
        numeric minimum_order_value
        numeric quantity_discount_min_qty
        numeric quantity_discount_rate
        varchar status
        text notes
        varchar certificate_documents
        varchar price_list
        varchar quotation_document
        varchar technical_brochure
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint rfq_id FK
        bigint supplier_id FK
    }
    
    purchase_supplierquotationitem {
        bigint id PK
        numeric quantity
        numeric unit_price
        numeric base_unit_price
        numeric item_discount_percentage
        numeric item_discount_amount
        varchar item_discount_type
        varchar item_discount_application
        numeric item_qty_discount_min
        numeric item_qty_discount_rate
        numeric total_amount
        int delivery_time_days
        numeric minimum_order_qty
        numeric package_qty
        numeric total_base_units
        text specifications
        bigint product_id FK
        bigint quotation_id FK
        bigint rfq_item_id FK
        bigint quoted_uom_id FK
    }
    
    purchase_purchaseorder {
        bigint id PK
        varchar po_number UK
        date order_date
        date expected_delivery_date
        text terms_conditions
        varchar payment_terms
        varchar delivery_terms
        numeric subtotal
        numeric tax_amount
        numeric total_amount
        numeric discount_amount
        varchar discount_type
        varchar discount_application
        numeric discount_percentage
        numeric discount_total
        numeric quantity_discount_min_qty
        numeric quantity_discount_rate
        numeric purchase_limit
        varchar status
        text notes
        timestamp approved_at
        varchar amendment_documents
        varchar purchase_order_document
        varchar supplier_agreement
        varchar technical_drawings
        timestamp created_at
        timestamp updated_at
        bigint approved_by_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint purchase_requisition_id FK
        bigint supplier_id FK
        bigint supplier_quotation_id FK
        bigint warehouse_id FK
    }
    
    purchase_purchaseorderitem {
        bigint id PK
        numeric quantity
        numeric unit_price
        numeric line_total
        numeric received_quantity
        date delivery_date
        numeric item_discount_amount
        varchar item_discount_application
        numeric item_discount_percentage
        varchar item_discount_type
        numeric item_qty_discount_min
        numeric item_qty_discount_rate
        numeric minimum_order_qty
        bigint product_id FK
        bigint purchase_order_id FK
        bigint quotation_item_id FK
        bigint uom_id FK
    }
    
    purchase_taxchargestemplate {
        bigint id PK
        varchar name
        varchar charge_type
        numeric rate
        boolean is_percentage
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
    }
    
    purchase_purchaseordertaxcharge {
        bigint id PK
        numeric amount
        bigint purchase_order_id FK
        bigint tax_template_id FK
    }
    
    purchase_goodsreceiptnote {
        bigint id PK
        varchar grn_number UK
        timestamp received_date
        varchar supplier_delivery_note
        varchar transporter
        varchar vehicle_number
        varchar driver_name
        varchar driver_phone
        varchar gate_entry_number
        numeric total_received_value
        varchar status
        text notes
        varchar delivery_challan
        varchar inspection_report
        varchar packing_list
        varchar photos_received_goods
        varchar quality_certificates
        timestamp inspection_assigned_at
        timestamp inspection_completed_at
        date inspection_due_date
        boolean requires_inspection
        boolean requires_quality_inspection
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint received_by_id FK
        bigint inspected_by_id FK
        bigint inspection_assigned_to_id FK
        bigint purchase_order_id FK
        bigint supplier_id FK
        bigint warehouse_id FK
    }
    
    purchase_grnitem {
        bigint id PK
        numeric ordered_qty
        numeric received_qty
        numeric accepted_qty
        numeric rejected_qty
        numeric returned_qty
        numeric unit_price
        numeric total_value
        varchar quality_status
        text remarks
        varchar location
        date expiry_date
        date manufacturer_date
        timestamp inspected_at
        text inspection_notes
        boolean tracking_required
        varchar tracking_type
        timestamp created_at
        timestamp updated_at
        bigint grn_id FK
        bigint product_id FK
        bigint warehouse_id FK
        bigint po_item_id FK
        bigint uom_id FK
        bigint inspector_id FK
    }
    
    purchase_grnitemtracking {
        bigint id PK
        varchar tracking_number
        varchar tracking_type
        varchar batch_number
        date manufacturing_date
        date expiry_date
        varchar supplier_batch_reference
        varchar quality_status
        text inspection_notes
        timestamp inspected_at
        varchar condition
        text defects
        text notes
        boolean is_available
        boolean is_locked
        varchar current_location
        timestamp created_at
        timestamp updated_at
        bigint grn_item_id FK
        bigint inspected_by_id FK
        bigint product_tracking_id FK
    }
    
    purchase_grninventorylock {
        bigint id PK
        numeric locked_quantity
        varchar lock_reason
        boolean is_active
        timestamp locked_at
        timestamp released_at
        text lock_notes
        text release_notes
        bigint grn_id FK
        bigint grn_item_id FK
        bigint locked_by_id FK
        bigint released_by_id FK
        bigint tracking_item_id FK
    }
    
    purchase_qualityinspection {
        bigint id PK
        varchar inspection_number UK
        varchar inspection_type
        timestamp assigned_at
        date due_date
        varchar status
        varchar priority
        text inspection_criteria
        varchar sampling_method
        int sample_size
        varchar overall_result
        numeric pass_percentage
        varchar inspection_report
        varchar photos
        varchar test_certificates
        timestamp started_at
        timestamp completed_at
        text notes
        text recommendations
        timestamp created_at
        timestamp updated_at
        bigint assigned_by_id FK
        bigint assigned_to_id FK
        bigint company_id FK
        bigint grn_id FK
    }
    
    purchase_qualityinspectionresult {
        bigint id PK
        numeric inspected_quantity
        numeric passed_quantity
        numeric failed_quantity
        varchar result
        jsonb defects_found
        varchar severity_level
        varchar action_taken
        text notes
        varchar photos
        timestamp inspected_at
        timestamp updated_at
        bigint grn_item_id FK
        bigint inspection_id FK
        bigint tracking_item_id FK
    }
    
    purchase_bill {
        bigint id PK
        varchar bill_number UK
        varchar supplier_invoice_number
        date bill_date
        date due_date
        numeric subtotal
        numeric tax_amount
        numeric total_amount
        numeric paid_amount
        numeric outstanding_amount
        varchar status
        boolean three_way_match_status
        text notes
        varchar approval_documents
        varchar supplier_invoice
        varchar supporting_documents
        varchar tax_invoice
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint grn_id FK
        bigint purchase_order_id FK
        bigint supplier_id FK
    }
    
    purchase_billitem {
        bigint id PK
        numeric quantity
        numeric unit_price
        numeric line_total
        bigint bill_id FK
        bigint product_id FK
        bigint grn_item_id FK
        bigint po_item_id FK
    }
    
    purchase_purchasepayment {
        bigint id PK
        varchar payment_number UK
        numeric amount
        date payment_date
        varchar payment_method
        varchar reference_number
        text notes
        varchar bank_statement
        varchar check_copy
        varchar payment_receipt
        varchar wire_transfer_advice
        timestamp created_at
        timestamp updated_at
        bigint bill_id FK
        bigint company_id FK
        bigint paid_by_id FK
        bigint supplier_id FK
    }
    
    purchase_purchasereturn {
        bigint id PK
        varchar return_number UK
        date return_date
        varchar return_type
        text reason
        numeric total_amount
        varchar status
        varchar photos_returned_items
        varchar quality_report
        varchar return_authorization
        varchar supplier_acknowledgment
        timestamp created_at
        timestamp updated_at
        bigint approved_by_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint grn_id FK
        bigint purchase_order_id FK
        bigint supplier_id FK
    }
    
    purchase_purchasereturnitem {
        bigint id PK
        numeric return_quantity
        numeric unit_price
        numeric line_total
        varchar condition_at_return
        boolean credit_note_requested
        text defects_description
        boolean packed_for_return
        boolean refund_requested
        boolean replacement_requested
        varchar resolution_status
        varchar return_reason
        date shipped_date
        boolean supplier_acknowledged
        timestamp created_at
        timestamp updated_at
        bigint grn_item_id FK
        bigint purchase_return_id FK
        bigint tracking_item_id FK
        bigint quality_result_id FK
    }
    
    purchase_purchaseapproval {
        bigint id PK
        varchar document_type
        int document_id
        numeric amount
        varchar status
        text comments
        timestamp approved_at
        timestamp created_at
        bigint approver_id FK
        bigint company_id FK
        bigint requested_by_id FK
    }
    
    %% ==========================================
    %% SALES MODULE
    %% ==========================================
    
    sales_product {
        bigint id PK
        varchar name
        text description
        varchar sku
        numeric price
        boolean is_service
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
    }
    
    sales_tax {
        bigint id PK
        varchar name
        numeric rate
        boolean is_active
        bigint company_id FK
    }
    
    sales_quotation {
        bigint id PK
        date date
        date valid_until
        numeric total
        varchar status
        text notes
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint customer_id FK
    }
    
    sales_quotationitem {
        bigint id PK
        numeric quantity
        numeric price
        numeric total
        bigint product_id FK
        bigint quotation_id FK
        bigint tax_id FK
    }
    
    sales_salesorder {
        bigint id PK
        date order_date
        date delivery_date
        text billing_address
        text shipping_address
        numeric total
        varchar status
        text notes
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint customer_id FK
        bigint quotation_id FK
    }
    
    sales_salesorderitem {
        bigint id PK
        numeric quantity
        numeric price
        numeric total
        bigint product_id FK
        bigint sales_order_id FK
        bigint tax_id FK
    }
    
    sales_invoice {
        bigint id PK
        date invoice_date
        date due_date
        numeric total
        varchar status
        varchar pdf_file
        text notes
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint customer_id FK
        bigint sales_order_id FK
    }
    
    sales_payment {
        bigint id PK
        numeric amount
        date payment_date
        varchar method
        varchar reference
        text notes
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint company_id FK
        bigint invoice_id FK
        bigint received_by_id FK
    }
    
    %% ==========================================
    %% HR MODULE
    %% ==========================================
    
    hr_department {
        bigint id PK
        varchar name
        varchar code
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint manager_id FK
    }
    
    hr_employee {
        bigint id PK
        varchar employee_id UK
        varchar first_name
        varchar last_name
        varchar email
        varchar phone
        varchar position
        date hire_date
        date termination_date
        numeric salary
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint department_id FK
        bigint user_id FK
    }
    
    hr_payroll {
        bigint id PK
        date period_start
        date period_end
        numeric basic_salary
        numeric overtime_hours
        numeric overtime_rate
        numeric bonuses
        numeric deductions
        numeric gross_salary
        numeric tax_deduction
        numeric net_salary
        varchar status
        timestamp created_at
        timestamp updated_at
        bigint employee_id FK
    }
    
    hr_leave {
        bigint id PK
        varchar leave_type
        date start_date
        date end_date
        int days
        text reason
        varchar status
        timestamp applied_at
        timestamp approved_at
        timestamp created_at
        timestamp updated_at
        bigint employee_id FK
        bigint approved_by_id FK
    }
    
    hr_attendance {
        bigint id PK
        date date
        time check_in
        time check_out
        numeric hours_worked
        varchar status
        text notes
        timestamp created_at
        timestamp updated_at
        bigint employee_id FK
    }
    
    %% ==========================================
    %% MANUFACTURING MODULE
    %% ==========================================
    
    manufacturing_billofmaterials {
        bigint id PK
        varchar name
        varchar version
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
        bigint product_id FK
    }
    
    manufacturing_billofmaterialsitem {
        bigint id PK
        numeric quantity
        varchar unit_of_measure
        text notes
        bigint bom_id FK
        bigint component_id FK
    }
    
    manufacturing_workorder {
        bigint id PK
        numeric quantity
        varchar status
        date scheduled_start
        date scheduled_end
        date actual_start
        date actual_end
        text notes
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint bom_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint product_id FK
    }
    
    manufacturing_productionplan {
        bigint id PK
        varchar plan_number UK
        date start_date
        date end_date
        varchar status
        text description
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint created_by_id FK
    }
    
    manufacturing_subcontractor {
        bigint id PK
        varchar specialization
        varchar capacity
        numeric quality_rating
        numeric delivery_rating
        int lead_time_days
        boolean is_active
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint partner_id FK
    }
    
    manufacturing_subcontractworkorder {
        bigint id PK
        numeric quantity
        numeric unit_cost
        numeric total_cost
        date start_date
        date due_date
        varchar status
        text notes
        timestamp created_at
        timestamp updated_at
        bigint company_id FK
        bigint product_id FK
        bigint subcontractor_id FK
        bigint work_order_id FK
    }
    
    %% ==========================================
    %% PROJECT MANAGEMENT MODULE
    %% ==========================================
    
    project_mgmt_project {
        bigint id PK
        varchar name
        text description
        varchar project_code UK
        date start_date
        date end_date
        numeric budget
        numeric actual_cost
        varchar status
        varchar priority
        timestamp created_at
        timestamp updated_at
        bigint account_id FK
        bigint client_id FK
        bigint company_id FK
        bigint created_by_id FK
        bigint project_manager_id FK
    }
    
    project_mgmt_task {
        bigint id PK
        varchar name
        text description
        varchar status
        varchar priority
        numeric estimated_hours
        numeric actual_hours
        date due_date
        timestamp created_at
        timestamp updated_at
        bigint assigned_to_contractor_id FK
        bigint assigned_to_employee_id FK
        bigint project_id FK
    }
    
    project_mgmt_timeentry {
        bigint id PK
        date date
        numeric hours
        text notes
        timestamp created_at
        bigint employee_id FK
        bigint task_id FK
    }
    
    project_mgmt_projectcontractor {
        bigint id PK
        varchar role
        numeric contract_amount
        date start_date
        date end_date
        boolean is_active
        timestamp created_at
        bigint contractor_id FK
        bigint project_id FK
    }
    
    project_mgmt_projectreport {
        bigint id PK
        varchar report_type
        date period_start
        date period_end
        timestamp generated_at
        text notes
        bigint project_id FK
    }
    
    %% ==========================================
    %% RELATIONSHIPS
    %% ==========================================
    
    %% User Auth Relationships
    user_auth_user ||--o{ user_auth_company : belongs_to
    user_auth_user ||--o{ user_auth_role : has
    user_auth_role ||--o{ user_auth_role : parent_of
    user_auth_user ||--o{ user_auth_user_groups : has
    user_auth_user ||--o{ user_auth_user_user_permissions : has
    user_auth_user ||--o{ user_auth_activitylog : creates
    
    %% Accounting Relationships
    user_auth_company ||--o{ accounting_accountcategory : owns
    accounting_accountcategory ||--o{ accounting_accountgroup : contains
    user_auth_company ||--o{ accounting_accountgroup : owns
    accounting_accountgroup ||--o{ accounting_account : contains
    user_auth_company ||--o{ accounting_account : owns
    accounting_account ||--o{ accounting_account : parent_of
    user_auth_company ||--o{ accounting_journalentry : owns
    user_auth_user ||--o{ accounting_journalentry : creates
    accounting_journalentry ||--o{ accounting_journalentryline : contains
    accounting_account ||--o{ accounting_journalentryline : used_in
    
    %% CRM Relationships
    user_auth_company ||--o{ crm_partner : owns
    user_auth_user ||--o{ crm_partner : creates
    user_auth_company ||--o{ crm_customer : owns
    user_auth_user ||--o{ crm_customer : creates
    accounting_account ||--o{ crm_customer : linked_to
    crm_partner ||--o{ crm_customer : extends
    
    %% Products Relationships
    user_auth_company ||--o{ products_productcategory : owns
    products_productcategory ||--o{ products_productcategory : parent_of
    user_auth_company ||--o{ products_attribute : owns
    products_attribute ||--o{ products_attributevalue : has
    user_auth_company ||--o{ products_product : owns
    user_auth_user ||--o{ products_product : creates
    user_auth_user ||--o{ products_product : updates
    products_productcategory ||--o{ products_product : categorizes
    products_product ||--o{ products_productvariant : has
    products_product ||--o{ products_productvariant : default_variant
    products_product ||--o{ products_productattribute : has
    products_attribute ||--o{ products_productattribute : defines
    products_product ||--o{ products_producttracking : tracks
    products_productvariant ||--o{ products_producttracking : tracks
    user_auth_user ||--o{ products_producttracking : creates
    inventory_warehouse ||--o{ products_producttracking : stores
    
    %% Inventory Relationships
    user_auth_company ||--o{ inventory_warehouse : owns
    user_auth_user ||--o{ inventory_warehouse : manages
    user_auth_company ||--o{ inventory_stockitem : owns
    accounting_account ||--o{ inventory_stockitem : linked_to
    products_product ||--o{ inventory_stockitem : tracked_as
    inventory_warehouse ||--o{ inventory_stockitem : stored_in
    user_auth_user ||--o{ inventory_stockmovement : creates
    products_product ||--o{ inventory_stockmovement : moves
    inventory_warehouse ||--o{ inventory_stockmovement : from_to
    products_product ||--o{ inventory_stocklot : batched_as
    inventory_warehouse ||--o{ inventory_stocklot : stored_in
    user_auth_user ||--o{ inventory_stockreservation : creates
    products_product ||--o{ inventory_stockreservation : reserves
    inventory_warehouse ||--o{ inventory_stockreservation : in
    
    %% Purchase Relationships
    user_auth_company ||--o{ purchase_unitofmeasure : defines
    user_auth_company ||--o{ purchase_supplier : owns
    user_auth_user ||--o{ purchase_supplier : creates
    crm_partner ||--o{ purchase_supplier : extends
    user_auth_company ||--o{ purchase_purchaserequisition : owns
    user_auth_user ||--o{ purchase_purchaserequisition : requests
    user_auth_user ||--o{ purchase_purchaserequisition : approves
    inventory_warehouse ||--o{ purchase_purchaserequisition : for
    purchase_purchaserequisition ||--o{ purchase_purchaserequisitionitem : contains
    products_product ||--o{ purchase_purchaserequisitionitem : requested
    purchase_supplier ||--o{ purchase_purchaserequisitionitem : preferred
    user_auth_company ||--o{ purchase_requestforquotation : owns
    user_auth_user ||--o{ purchase_requestforquotation : creates
    purchase_purchaserequisition ||--o{ purchase_requestforquotation : generates
    inventory_warehouse ||--o{ purchase_requestforquotation : for
    purchase_requestforquotation ||--o{ purchase_requestforquotation_suppliers : sent_to
    purchase_supplier ||--o{ purchase_requestforquotation_suppliers : receives
    purchase_requestforquotation ||--o{ purchase_rfqitem : contains
    products_product ||--o{ purchase_rfqitem : quoted
    purchase_unitofmeasure ||--o{ purchase_rfqitem : measured_in
    user_auth_company ||--o{ purchase_supplierquotation : owns
    purchase_requestforquotation ||--o{ purchase_supplierquotation : responds_to
    purchase_supplier ||--o{ purchase_supplierquotation : provides
    purchase_supplierquotation ||--o{ purchase_supplierquotationitem : contains
    products_product ||--o{ purchase_supplierquotationitem : quotes
    purchase_rfqitem ||--o{ purchase_supplierquotationitem : responds_to
    purchase_unitofmeasure ||--o{ purchase_supplierquotationitem : measured_in
    user_auth_company ||--o{ purchase_purchaseorder : owns
    user_auth_user ||--o{ purchase_purchaseorder : creates
    user_auth_user ||--o{ purchase_purchaseorder : approves
    purchase_purchaserequisition ||--o{ purchase_purchaseorder : generates
    purchase_supplier ||--o{ purchase_purchaseorder : supplies
    purchase_supplierquotation ||--o{ purchase_purchaseorder : based_on
    inventory_warehouse ||--o{ purchase_purchaseorder : delivered_to
    purchase_purchaseorder ||--o{ purchase_purchaseorderitem : contains
    products_product ||--o{ purchase_purchaseorderitem : ordered
    purchase_supplierquotationitem ||--o{ purchase_purchaseorderitem : based_on
    purchase_unitofmeasure ||--o{ purchase_purchaseorderitem : measured_in
    user_auth_company ||--o{ purchase_taxchargestemplate : defines
    accounting_account ||--o{ purchase_taxchargestemplate : linked_to
    purchase_purchaseorder ||--o{ purchase_purchaseordertaxcharge : has
    purchase_taxchargestemplate ||--o{ purchase_purchaseordertaxcharge : applied_as
    user_auth_company ||--o{ purchase_goodsreceiptnote : owns
    user_auth_user ||--o{ purchase_goodsreceiptnote : receives
    user_auth_user ||--o{ purchase_goodsreceiptnote : inspects
    user_auth_user ||--o{ purchase_goodsreceiptnote : assigns_inspection
    purchase_purchaseorder ||--o{ purchase_goodsreceiptnote : received_for
    purchase_supplier ||--o{ purchase_goodsreceiptnote : delivers
    inventory_warehouse ||--o{ purchase_goodsreceiptnote : received_at
    purchase_goodsreceiptnote ||--o{ purchase_grnitem : contains
    products_product ||--o{ purchase_grnitem : received
    inventory_warehouse ||--o{ purchase_grnitem : stored_in
    purchase_purchaseorderitem ||--o{ purchase_grnitem : fulfills
    purchase_unitofmeasure ||--o{ purchase_grnitem : measured_in
    user_auth_user ||--o{ purchase_grnitem : inspects
    purchase_grnitem ||--o{ purchase_grnitemtracking : tracks
    user_auth_user ||--o{ purchase_grnitemtracking : inspects
    products_producttracking ||--o{ purchase_grnitemtracking : linked_to
    purchase_goodsreceiptnote ||--o{ purchase_grninventorylock : locks
    purchase_grnitem ||--o{ purchase_grninventorylock : locks
    user_auth_user ||--o{ purchase_grninventorylock : locks
    user_auth_user ||--o{ purchase_grninventorylock : releases
    purchase_grnitemtracking ||--o{ purchase_grninventorylock : tracks
    user_auth_company ||--o{ purchase_qualityinspection : owns
    user_auth_user ||--o{ purchase_qualityinspection : assigns
    user_auth_user ||--o{ purchase_qualityinspection : performs
    purchase_goodsreceiptnote ||--o{ purchase_qualityinspection : inspects
    purchase_qualityinspection ||--o{ purchase_qualityinspectionresult : produces
    purchase_grnitem ||--o{ purchase_qualityinspectionresult : tests
    purchase_grnitemtracking ||--o{ purchase_qualityinspectionresult : tracks
    user_auth_company ||--o{ purchase_bill : owns
    user_auth_user ||--o{ purchase_bill : creates
    purchase_goodsreceiptnote ||--o{ purchase_bill : invoiced_for
    purchase_purchaseorder ||--o{ purchase_bill : based_on
    purchase_supplier ||--o{ purchase_bill : invoices
    purchase_bill ||--o{ purchase_billitem : contains
    products_product ||--o{ purchase_billitem : billed
    purchase_grnitem ||--o{ purchase_billitem : based_on
    purchase_purchaseorderitem ||--o{ purchase_billitem : references
    user_auth_company ||--o{ purchase_purchasepayment : owns
    user_auth_user ||--o{ purchase_purchasepayment : pays
    purchase_bill ||--o{ purchase_purchasepayment : pays_for
    purchase_supplier ||--o{ purchase_purchasepayment : paid_to
    user_auth_company ||--o{ purchase_purchasereturn : owns
    user_auth_user ||--o{ purchase_purchasereturn : creates
    user_auth_user ||--o{ purchase_purchasereturn : approves
    purchase_goodsreceiptnote ||--o{ purchase_purchasereturn : returns_from
    purchase_purchaseorder ||--o{ purchase_purchasereturn : references
    purchase_supplier ||--o{ purchase_purchasereturn : returned_to
    purchase_purchasereturn ||--o{ purchase_purchasereturnitem : contains
    purchase_grnitem ||--o{ purchase_purchasereturnitem : returns
    purchase_grnitemtracking ||--o{ purchase_purchasereturnitem : tracks
    purchase_qualityinspectionresult ||--o{ purchase_purchasereturnitem : based_on
    user_auth_company ||--o{ purchase_purchaseapproval : owns
    user_auth_user ||--o{ purchase_purchaseapproval : approves
    user_auth_user ||--o{ purchase_purchaseapproval : requests
    
    %% Sales Relationships
    user_auth_company ||--o{ sales_product : owns
    user_auth_company ||--o{ sales_tax : defines
    user_auth_company ||--o{ sales_quotation : owns
    user_auth_user ||--o{ sales_quotation : creates
    crm_customer ||--o{ sales_quotation : requests
    sales_quotation ||--o{ sales_quotationitem : contains
    products_product ||--o{ sales_quotationitem : quotes
    sales_tax ||--o{ sales_quotationitem : applies_to
    user_auth_company ||--o{ sales_salesorder : owns
    user_auth_user ||--o{ sales_salesorder : creates
    crm_customer ||--o{ sales_salesorder : orders
    accounting_account ||--o{ sales_salesorder : linked_to
    sales_quotation ||--o{ sales_salesorder : converts_to
    sales_salesorder ||--o{ sales_salesorderitem : contains
    products_product ||--o{ sales_salesorderitem : ordered
    sales_tax ||--o{ sales_salesorderitem : applies_to
    user_auth_company ||--o{ sales_invoice : owns
    user_auth_user ||--o{ sales_invoice : creates
    crm_customer ||--o{ sales_invoice : billed_to
    accounting_account ||--o{ sales_invoice : linked_to
    sales_salesorder ||--o{ sales_invoice : invoices
    user_auth_company ||--o{ sales_payment : owns
    user_auth_user ||--o{ sales_payment : receives
    accounting_account ||--o{ sales_payment : deposited_to
    sales_invoice ||--o{ sales_payment : pays_for
    
    %% HR Relationships
    user_auth_company ||--o{ hr_department : owns
    user_auth_user ||--o{ hr_department : manages
    user_auth_company ||--o{ hr_employee : employs
    hr_department ||--o{ hr_employee : contains
    user_auth_user ||--o{ hr_employee : linked_to
    hr_employee ||--o{ hr_payroll : receives
    hr_employee ||--o{ hr_leave : takes
    user_auth_user ||--o{ hr_leave : approves
    hr_employee ||--o{ hr_attendance : records
    
    %% Manufacturing Relationships
    user_auth_company ||--o{ manufacturing_billofmaterials : owns
    user_auth_user ||--o{ manufacturing_billofmaterials : creates
    products_product ||--o{ manufacturing_billofmaterials : produces
    manufacturing_billofmaterials ||--o{ manufacturing_billofmaterialsitem : contains
    products_product ||--o{ manufacturing_billofmaterialsitem : component
    user_auth_company ||--o{ manufacturing_workorder : owns
    user_auth_user ||--o{ manufacturing_workorder : creates
    accounting_account ||--o{ manufacturing_workorder : linked_to
    manufacturing_billofmaterials ||--o{ manufacturing_workorder : follows
    products_product ||--o{ manufacturing_workorder : produces
    user_auth_company ||--o{ manufacturing_productionplan : owns
    user_auth_user ||--o{ manufacturing_productionplan : creates
    user_auth_company ||--o{ manufacturing_subcontractor : owns
    crm_partner ||--o{ manufacturing_subcontractor : extends
    user_auth_company ||--o{ manufacturing_subcontractworkorder : owns
    products_product ||--o{ manufacturing_subcontractworkorder : produces
    manufacturing_subcontractor ||--o{ manufacturing_subcontractworkorder : performs
    manufacturing_workorder ||--o{ manufacturing_subcontractworkorder : subcontracts
    
    %% Project Management Relationships
    user_auth_company ||--o{ project_mgmt_project : owns
    user_auth_user ||--o{ project_mgmt_project : creates
    accounting_account ||--o{ project_mgmt_project : linked_to
    crm_partner ||--o{ project_mgmt_project : client
    hr_employee ||--o{ project_mgmt_project : manages
    project_mgmt_project ||--o{ project_mgmt_task : contains
    crm_partner ||--o{ project_mgmt_task : assigned_to
    hr_employee ||--o{ project_mgmt_task : assigned_to
    hr_employee ||--o{ project_mgmt_timeentry : logs
    project_mgmt_task ||--o{ project_mgmt_timeentry : tracked_for
    project_mgmt_project ||--o{ project_mgmt_projectcontractor : engages
    crm_partner ||--o{ project_mgmt_projectcontractor : contractor
    project_mgmt_project ||--o{ project_mgmt_projectreport : generates
    
    %% Cross-module relationships
    purchase_supplier ||--o{ products_producttracking : supplies
    purchase_grnitem ||--o{ products_producttracking : creates
```

## Module Breakdown

### 1. **User Authentication & Company Management**
- `user_auth_company`: Company/tenant management
- `user_auth_role`: Role-based access control
- `user_auth_user`: User accounts with company and role associations
- `user_auth_activitylog`: Audit trail for user actions

### 2. **Accounting Module**
- Complete Chart of Accounts structure (Categories → Groups → Accounts)
- Double-entry bookkeeping with journal entries and lines
- Integration with all financial transactions

### 3. **CRM Module**
- `crm_partner`: Base entity for customers, suppliers, contractors
- `crm_customer`: Customer-specific information and credit management

### 4. **Products Module**
- Hierarchical product categories
- Product attributes and variants
- Advanced product tracking (serial numbers, batches, expiry dates)
- Support for manufactured, purchased, and service products

### 5. **Inventory Module**
- Multi-warehouse support
- Real-time stock tracking
- Stock movements and reservations
- Lot/batch management

### 6. **Purchase Module**
- Complete procurement cycle: PR → RFQ → Quotation → PO → GRN → Bill → Payment
- Quality inspection workflows
- Purchase returns and approvals
- Advanced supplier management

### 7. **Sales Module**
- Sales quotations, orders, and invoices
- Tax calculations and payment tracking
- Integration with accounting module

### 8. **HR Module**
- Employee management with departments
- Payroll processing
- Leave management and attendance tracking

### 9. **Manufacturing Module**
- Bill of Materials (BOM) management
- Work order processing
- Subcontractor management
- Production planning

### 10. **Project Management Module**
- Project lifecycle management
- Task assignment and time tracking
- Contractor engagement
- Project reporting

## Key Features

- **Multi-tenant Architecture**: Company-based data isolation
- **Role-based Access Control**: Hierarchical role management
- **Complete Audit Trail**: Activity logging for all operations
- **Document Management**: File attachments for various documents
- **Quality Control**: Inspection workflows and quality tracking
- **Financial Integration**: All transactions linked to accounting
- **Advanced Tracking**: Serial numbers, batches, expiry dates
- **Workflow Management**: Approval processes for critical operations

This schema supports a comprehensive ERP system with all major business functions integrated and properly related.
