DEPARTMENTS = {

    # =====================================================
    # SALES & MARKETING (HAS SUB-DEPARTMENTS)
    # =====================================================
    "sales_marketing": {
        "label": "Sales & Marketing",
        "has_subdepartments": True,
        "subdepartments": {

            "Sales": {
                "label": "LED",
                "kras": {
                    "inventory_&_supply_chain_mgmt": {
                        "label": "Inventory and Supply Chain Managemen",
                        "kpis": ["inventory_dormancy"]
                    }
                }
            },

            "marketing": {
                "label": "Marketing",
                "kras": {
                    "vendor_management": {
                        "label": "Vendor Management",
                        "kpis": ["vendor_ontime"]
                    },
                    "seasonal_campaign_execution": {
                        "label": "Seasonal Campaign Execution",
                        "kpis": ["rm_po_sla"]
                    }
                }
            },

            "procurement_&_vendor_management": {
                "label": "Procurement & Vendor Management",
                "kras": {
                    "business_development": {
                        "label": "Business Development",
                        "kpis": ["vendor_performance"]
                    },
                    "cost_optimization": {
                        "label": "Cost Optimization",
                        "kpis": ["pm_shortage"]

                    }
                }
            },

            "packaging": {
                "label": "Packaging",
                "kras": {
                    "cost_optimization": {
                        "label": "Cost Optimization",
                        "kpis": ["supply_availability"]

                    }
                }
            }
        }
    },

    # =====================================================
    # PURCHASE (NO SUB-DEPARTMENTS)
    # =====================================================
    "purchase": {
        "label": "Purchase",
        "has_subdepartments": False,
        "kras": {

            "order_delivery_tracking": {
                "label": "Order Delivery Tracking",
                "kpis": ["order_delivery"]
            },

            "sales_order_management": {
                "label": "Sales Order Management",
                "kpis": [ "sales_invoice" ]
            },

            "sales_order_&_invoice_management": {
                "label": "Sales Order & Invoice Management",
                "kpis": ["short_closed_so"]
            },

            "internal_raw_material_transfer": {
                "label": "Internal Raw Material Transfer",
                "kpis": ["transfers"]
            }
        }
    }
}
