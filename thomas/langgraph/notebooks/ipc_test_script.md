```markdown
# IPC Test Script

## Manage General Settings
1. **Activate Internal Sales Orders**
    - Access 'Feature List. Open' (CMS975)
    - Toggle on NCR 11589 and NCR 11604

2. **Configure Stock Messages**
    - Access 'Order Init Stock Trans Qualif' (MHS860)
        - Generate all with F14
        - Use Qualifier 29
    - Access 'Stock Msg Partner. Open' (MMS865)
        - Set Stock message partner to Whs Msg Partner
        - Set type to I
        - Set Msg type to WMS
    - Access 'Settings - Deliveries' (CRS721)
        - Set Partner to WS
        - Set Message type to WMS
    - Access 'Number Series. Open' (CRS165)
        - Set Series type 17, number series 1 for order-initiated stock messages

3. **Manage Deviations**
    - Access 'Settings – Application Messages' (CRS424)
        - Activate messages for deviations: 210, 211, 212
    - Access 'Settings – Purchasing' (CRS780)
        - Set Tolerances at Division level

## Manage PO Settings
1. **Define PO Type**
    - Access 'Purchase Order Type. Open' (PPS095)
        - Configure Order type I01
        - Set Goods receiving method to (direct put-away)
        - Adjust PO status, automatic printout, etc.

2. **Define Suppliers**
    - Access 'Supplier Group. Open' (CRS150)
    - Access 'Supplier. Open' (CRS620)
    - Access 'Supplier. Define Purchase & Financial' (CRS624)
    - Access 'Supplier. Connect our Customer Number' (CRS680)
    - Access 'Purchase Agreement. Open' (PPS100)

3. **Define PO Charges**
    - Access 'Settings – Purchasing' (CRS780)
    - Access 'Costing Element. Open' (PPS280)
    - Access 'Purchase Costing Model. Open' (PPS285)

4. **Stage Package**
    - Access 'Settings – Purchasing' (CRS780)

5. **Perform Other PO Related Settings**
    - Access 'Subsystem Job. Open' (MNS051)

## Manage Internal CO Settings
1. **Define CO Charges**
    - Access 'CO Charge. Open' (OIS030)

2. **Define Delivery Terms and Goods Responsibility**
    - Access 'Delivery Term. Open' (CRS065)

3. **Define CO Type**
    - Access 'Dispatch Policy. Open' (MWS010)
    - Access 'CO Type. Open' (OIS010)

## Define Customers
1. **Define Customer Group**
    - Access 'Customer Group. Open' (CRS145)
    - Access 'Customer. Open' (CRS610)

2. **Generate Standard Fields**
    - Access 'Field Group. Display Permitted Fields' (CRS109)

3. **Enable Batch Orders**
    - Access 'Settings – Batch Orders' (OIS278)

## Manage Item Settings
1. **Connect Warehouse for Item**
    - Access 'Item. Connect Warehouse' (MMS002)

2. **Connect Facility for Item**
    - Access 'Item. Connect Facility' (MMS003)
    - Access 'Purchase Agreement. Open Lines' (PPS101)

## Manage Goods-in-transit Settings
1. **Enable Goods-in-transit**
    - Access 'Settings – Cost Accounting' (CAS900)

2. **Define Accounts**
    - Access 'Accounting Identity. Open' (CRS630)

3. **Define Accounting Rules**
    - Access 'Number Series. Open' (CRS165)
    - Access 'Accounting Event. Open' (CRS375)
    - Access 'Accounting Type. Open' (CRS385)
    - Access 'Accounting Rule. Open' (CRS395)

## Test Variants
- Check all setup with example internal customer and supplier
- Set delivery terms and goods responsibility code

## Tips and Hints
- Kits usage details
- Attributes setup requirements
- QMS support information
- Historic Actual Cost and Goods-in-transit details
- Line Charges setup
- Supply Chain Orders considerations
- Transportation lead time details
```

This markdown script provides a structured guide for the IPC test covering the various configurations and settings outlined in the given context.