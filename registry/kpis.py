"""
KPI_REGISTRY

Maps:
KPI ID → UI label → required Excel files → logic module → function → charts

⚠️ KPI IDs MUST match:
- registry/hierarchy.py
- Flask routes
"""

KPI_REGISTRY = {

    # =====================================================
    # INVENTORY / SUPPLY CHAIN
    # =====================================================
    "inventory_dormancy": {
        "label": "% of slow-moving / dead inventory vs total stock",
        "files": ["item_ledger"],
        "module": "component2_inventory",
        "function": "run_component2",

        "charts": [
            {
                "type": "donut",
                "column": "Inventory_Status",
                "title": "Inventory Status Distribution"
            },
            {
                "type": "bar",
                "x": "Item_Category",
                "y": "Quantity",
                "title": "Inventory by Category"
            }
        ]
    },

    # =====================================================
    # VENDOR MANAGEMENT
    # =====================================================
    "vendor_ontime": {
        "label": "95% on-time delivery rate from vendors",
        "files": [
            "purchase_orders",
            "purchase_receipts",
            "purchase_lines"
        ],
        "module": "component3a_vendor_ontime",
        "function": "run_component3a",

        "charts": [
            {
                "type": "donut",
                "column": "Delivery_Status",
                "title": "Vendor Delivery Status"
            },
            {
                "type": "stacked_bar",
                "x": "Month",
                "color": "Delivery_Status",
                "title": "Monthly Vendor Delivery Performance"
            }
        ]
    },

    "vendor_performance": {
        "label": "Track and evaluate vendor performance regularly",
        "files": ["vendor_performance"],
        "module": "component3c_vendor_performance",
        "function": "run_component3c",

        "charts": [
            {
                "type": "bar",
                "x": "Vendor",
                "y": "Performance_Score",
                "title": "Vendor Performance Scores"
            }
        ]
    },

    # =====================================================
    # PURCHASE / ORDER DELIVERY
    # =====================================================
    "order_delivery": {
        "label": "% of deliveries received on time",
        "files": [
            "purchase_orders",
            "purchase_receipts",
            "purchase_lines"
        ],
        "module": "component3b_order_delivery",
        "function": "run_component3b",

        "charts": [
            {
                "type": "donut",
                "column": "Status",
                "title": "Delivery Status Distribution"
            },
            {
                "type": "stacked_bar",
                "x": "Month",
                "color": "Status",
                "title": "Monthly Delivery Status"
            }
        ]
    },

    # =====================================================
    # SALES ORDER & INVOICE
    # =====================================================
    "short_closed_so": {
        "label": "% of pending short closed for shipment completed SOs",
        "files": ["sales_orders"],
        "module": "component6_short_closed_so",
        "function": "run_component6",

        "charts": [
            {
                "type": "donut_summary",
                "labels": ["Short Closed", "Not Short Closed"],
                "values": ["Short_Closed", "Not_Short_Closed"],
                "title": "Short Closed SO Distribution"
            },
            {
                "type": "bar",
                "x": "Month",
                "y": "Short_Closed",
                "title": "Short Closed SOs by Month"
            }
        ]
    },

    # =====================================================
    # INTERNAL TRANSFERS
    # =====================================================
    "transfers": {
        "label": "% of transfer orders completed on schedule",
        "files": ["transfer_lines"],
        "module": "component1_transfers",
        "function": "run_component1",

        "charts": [
            {
                "type": "donut",
                "column": "Status",
                "title": "Order Status Distribution"
            },
            {
                "type": "stacked_bar",
                "x": "Month",
                "color": "Status",
                "title": "Monthly Transfer Order Status"
            }
        ]
    },

    # =====================================================
    # PURCHASE ORDER SLA
    # =====================================================
    "po_sla": {
        "label": "Purchase Order SLA",
        "files": [
            "purchase_orders",
            "purchase_receipts",
            "purchase_lines"
        ],
        "module": "component5_po_sla",
        "function": "run_component5",

        "charts": [
            {
                "type": "donut",
                "column": "SLA_Status",
                "title": "PO SLA Compliance"
            },
            {
                "type": "bar",
                "x": "Month",
                "y": "Delay_Days",
                "title": "PO SLA Delay Trend"
            }
        ]
    },

    # =====================================================
    # RM PO SLA (QUARTERLY)
    # =====================================================
    "rm_po_sla": {
        "label": "100% RM requisitions fulfilled within defined SLA",
        "files": [
            "items",
            "purchase_orders",
            "purchase_receipts",
            "purchase_lines"
        ],
        "module": "component5a_rm_quarterly",
        "function": "run_component5a_rm",

        "charts": [
            {
                "type": "donut",
                "column": "SLA_Status",
                "title": "RM PO SLA Compliance"
            }
        ]
    },

    # =====================================================
    # COST OPTIMIZATION / PACKAGING
    # =====================================================
    "cost_optimization": {
        "label": "100% supply availability / zero production stoppages",
        "files": [
            "items",
            "item_ledger"
        ],
        "module": "component7_cost_optimization",
        "function": "run_component7",

        "charts": [
            {
                "type": "bar",
                "x": "Item",
                "y": "Stock_Level",
                "title": "Item Stock Levels"
            }
        ]
    },

    # =====================================================
    # SALES INVOICE (O2C)
    # =====================================================
    "sales_invoice": {
        "label": "Sales Order to Invoice Completion (O2C)",
        "files": [
            "sales_orders",
            "sales_invoices"
        ],
        "module": "component4_sales_invoice",
        "function": "run_component4",

        "charts": [
            {
                "type": "stacked_bar",
                "x": "Month",
                "color": "Invoice_Status",
                "title": "O2C Invoice Completion Trend"
            }
        ]
    }
}
