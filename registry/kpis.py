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
    "template": "component2.html",
    "table_columns": [
            "Item No.",
            "Location Code",
            "Description",
            "Category",
            "Subcategory",
            "On_Hand",
            "Stock_Value",
            "Last Outward Date",
            "Status",
            "Days Dormant",
            "Days Dormant Display"
        ],
    "charts":[
   {
      "type": "donut_value",
  "column": "Status",
  "value": "Stock_Value",
  "title": "Inventory Stock Status"
},
        
      
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
    "template": "component3a_vendor_management.html",
    "table_columns": [
            "Vendor",
            "Total_POs",
            "On_Time_POs",
            "Late_POs",
            "On_Time_Pct"
        ],

    "charts": [
    {
        "type": "bar",
        "x": "Bucket",
        "y": "Vendor Count",
        "title": "Vendors by PO Completion Rate"
    }
]
},


    "vendor_performance": {
    "label": "Track and evaluate vendor performance regularly",
    "files": ["purchase_orders",
        "purchase_receipts",
        "purchase_lines"],
    "module": "component3c_vendor_performance",
    "function": "run_component3c",
    "template": "component3c_vendor_performance.html",
    "table_columns": [
            "Vendor",
            "Total_POs",
            "On_Time_POs",
            "Late_POs",
            "On_Time_Pct"
        ],
    "charts": [
        {
        "type": "bar",
        "x": "Bucket",
        "y": "Vendor Count",
        "title": "Vendors by PO Completion Rate"
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
        "template": "component3b_order_delivery.html",
        "table_columns": [
            "PO_No",
            "Vendor",
            "Order_Date",
            "Last_Receiving_No",
            "Last_Receipt_Date",
            "Outstanding_Qty",
            "Days_Difference",
            "Delivery_Status",
            "Month"
        ],

        "charts": [
        {
            "type": "donut",
            "column": "Delivery_Status",
            "title": "PO Status : On-Time(<=15 Days) vs Delayed Deliveries(>15 Days) vs No-Receipt"
        }
    ]
    },

    # =====================================================
    # SALES ORDER & INVOICE
    # =====================================================
    "short_closed_so": {
    "label": "% of pending short closed for non shipped SOs",
    "files": ["sales_orders"],
    "module": "component6_short_closed_so",
    "function": "run_component6",
    "template": "component6.html",
    "table_columns": [
            "Total_Non_Shipped",
            "Month",
            "Short_Closed",
            "Not_Short_Closed"
        ],

    "charts": [
        {
            "type": "donut_summary",
            "labels": ["Short Closed", "Not Short Closed"],
            "values": ["Short_Closed", "Not_Short_Closed"],
            "title": "Short Closed vs Not Short Closed Sales Orders"
        },
        {
            "type": "bar",
            "x": "Month",
            "y": "Short_Closed",
            "title": "Month on Month Short Closed Orders"
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
        "template": "component1.html",
        "table_columns": [
            "Document No",
            "Total Qty",
            "Shipped Qty",
            "Received Qty",
            "In Transit Qty",
            "Status",
            "Month"
        ],
        "charts": [
            {
                "type": "donut",
                "column": "Status",
                "title": "Transfer Order Status"
            },
            {
                "type": "stacked_bar",
                "x": "Month",
                "color": "Status",
                "title": "Month on Month Transfer Order Status"
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
        "template": "component5.html",
        "charts": [
            {
                "type": "donut",
                  "column": "On_Time",
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
    "template": "component5a_rm.html",
    "table_columns": [
            "PO_No",
            "Vendor",
            "Order_Date",
            "Last_Receipt_Date",
            "Days_To_Receive",
            "Order_Quarter",
            "On_Time"
        ],
    "charts": [
        {          
            "type": "donut",
            "column": "On_Time",
            "title": "RM PO Delivery Status (%)"
        },
       
    ]
},

#     # =====================================================
#     # COST OPTIMIZATION / PACKAGING
#     # =====================================================
# "cost_optimization": {
#     "label": "100% supply availability / zero production stoppages",
#     "files": ["items", "item_ledger"],
#     "module": "component7_cost_optimization",
#     "function": "run_component7",
#     "template": "component7a_supply_availability.html",
#     "table_columns": [
#             "Item_No",
#             "Description",
#             "Location Code",
#             "Stock_Qty",
#             "Status"
#         ],
#     "charts": [
#         {
#     "type": "donut_value",
#     "column": "Stock_Status",
#     "value": "Count",
#     "title": "PM Stock Status",
#     "colors": {
#                 "RED": "#e74c3c",
#                 "YELLOW": "#f1c40f",
#                 "GREEN": "#2ecc71"
#                 }
#         }
#     ]
# },
"supply_availability": {
    "label": "100% supply availability",
    "files": ["items", "item_ledger"],
    "module": "component7_cost_optimization",
    "function": "run_component7",
    "template": "component7a_supply_availability.html",
    "observation": "Supply availability",

    # ⭐ ALL STOCK (no filtering)
    "filter": None,

    "table_columns": [
        "Item_No",
        "Description",
        "Location Code",
        "Stock_Qty",
        "Status"
    ],
    "charts": [
               {
            "type": "bar_horizontal",
            "x": "Percentage",
            "y": "Stock_Status",
            "title": "Stock Status Distribution",
            "text": "Percentage",
            "orientation": "h"
            }
    ]
},
"pm_shortage": {
    "label": "Zero production stoppages due to packaging shortages",
    "files": ["items", "item_ledger"],
    "module": "component7_cost_optimization",
    "function": "run_component7",
    "template": "component7a_supply_availability.html",
     "observation": "PM Stuff",
    # ⭐ PM ONLY filtering
    "filter": "PM",

    "table_columns": [
        "Item_No",
        "Description",
        "Location Code",
        "Stock_Qty",
        "Status"
    ],
    "charts": [
        {
            "type": "bar_horizontal",
            "x": "Percentage",
            "y": "Stock_Status",
            "title": "Stock Status Distribution",
            "text": "Percentage",
            "orientation": "h"
            }
        
    ]
},




    # =====================================================
    # SALES INVOICE (O2C)
    # =====================================================
    "sales_invoice": {
    "label": "Sales Order to Shipment Completion",
    "files": ["sales_orders", "sales_invoices"],
    "module": "component4_sales_invoice",
    "function": "run_component4",
    "template": "component4.html",
    "table_columns": [
            "Sales Order No",
            "Sales Order Date",
            "Completely_Shipped",
            "Final Invoice Date",
            "O2C Cycle Days"
        ],
     "charts": [
       {
    "type": "bar",
    "x": "SLA Bucket",
    "y": "SLA %",
    "title": "SO to Shipment Completion"
}

    ]
}

}
