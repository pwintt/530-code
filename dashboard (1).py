import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
from box_utils import Box, assign_boxes, calculate_outlier_rate, calculate_weighted_void_rate

# Input data files   
with st.sidebar:
    st.header("Data Configuration")
    st.subheader("Upload Data Files")
    box_data_fn = st.file_uploader("Upload current_boxes.csv", type=['csv'],key="box_uploader" )
    returns_data_fn = st.file_uploader("Upload returns_data.csv", type=['csv'],key="returns_uploader")
if box_data_fn is None or returns_data_fn is None:
    st.warning("Please upload both current_boxes.csv and returns_data.csv to continue.")
    st.stop()

box_df = pd.read_csv(box_data_fn)
returns_df = pd.read_csv(returns_data_fn)
df = returns_df.set_index('sku_id')
df_2 = box_df.set_index('box_id')


df.loc[:,'volume']= df.loc[:,'l'] * df.loc[:,'w'] * df.loc[:,'h'] / 1000000
dim_1, dim_2, dim_3 = [],[],[]
for sku_id, row in df.iterrows():
    dims= sorted([row['l'], row['w'], row['h']], reverse=True)
    dim_1.append(dims[0])
    dim_2.append(dims[1])
    dim_3.append(dims[2])
df.loc[:,'dim_1'] = dim_1
df.loc[:,'dim_2'] = dim_2
df.loc[:,'dim_3'] = dim_3

#put box data into Box class
current_boxes = []
for box_id, row in df_2.iterrows():
    current_boxes.append(Box(row['l'], row['w'], row['h'], box_id=box_id))

#use assign_boxes to make a list to store the outcome of the box
assigned_boxes = assign_boxes(df, current_boxes, return_index=False)
df.loc[:,'box'] = assigned_boxes

#generate a new column of box volume in df_2
df_2.loc[:,'box_volume'] = df_2.loc[:,'l']* df_2.loc[:,'w']*df_2.loc[:,'h']/1000000

#put the box volume in df 
box_volume =[]
for sku_id, row in df.iterrows():
    if pd.isna(row['box']):
        box_volume.append(None)
    else:
        box_volume.append(df_2.loc[row['box'],'box_volume'])
df.loc[:,'box volume'] = box_volume

#calculate void fill rate 
void_fill_rate = (df.loc[:,'box volume'] - df.loc[:,'volume'])/df.loc[:,'box volume']
df.loc[:,'void fill rate'] =void_fill_rate

#calculate current void fill volume
total_void_vol_per_sku = (df['box volume'] - df['volume']) * df['quantity']
is_packed = pd.notna(df['box'])
total_packed_qty = df.loc[is_packed, 'quantity'].sum()
average_current_void_volume = total_void_vol_per_sku.sum() / total_packed_qty

#calculate outlier rate 
outlier_rate = calculate_outlier_rate(df, 'box')

#calculate weighted average void fill rate 
weighted_avr_void_rate = calculate_weighted_void_rate(df, 'void fill rate', 'box')

#calculate total used surface area
df_2.loc[:,'box_surface_area'] = 2 * (df_2.loc[:,'l']*df_2.loc[:,'w'] + df_2.loc[:,'l']*df_2.loc[:,'h'] + df_2.loc[:,'w']*df_2.loc[:,'h'])
df.loc[:,'box surface area'] = df['box'].map(df_2['box_surface_area'])
used_surface_area= df.loc[:,'box surface area'] * df.loc[:,'quantity']/1000000
df.loc[:,'used surface area per sku'] = used_surface_area
total_used_surface_area = df.loc[:,'used surface area per sku'].sum(skipna=True)

#design new range of box 
#make a 3 side quantile df as new box and use int 
quantiles = [0.19, 0.38, 0.57, 0.76, 0.95]
new_box_objects = [] 
for i, q in enumerate(quantiles): 
    l_new = math.ceil(df['dim_1'].quantile(q))
    w_new = math.ceil(df['dim_2'].quantile(q))
    h_new = math.ceil(df['dim_3'].quantile(q))
    new_box_objects.append(Box(l_new, w_new, h_new))
max_l = math.ceil(df['dim_1'].max())
max_w = math.ceil(df['dim_2'].max())
max_h = math.ceil(df['dim_3'].max())
new_box_objects.append(Box(max_l,max_w, max_h))
new_boxes_data = []
for b in new_box_objects:
    new_boxes_data.append({'l': b.l, 'w': b.w, 'h': b.h, 'box_volume': b.volume()}) 
new_boxes_df = pd.DataFrame(new_boxes_data)

#check new weight avr void fill rate and outlier rate 
new_assigned_boxes = assign_boxes(df, new_box_objects, return_index=True)
df.loc[:,'new assigned box'] = new_assigned_boxes

new_box_volume =[]
for sku_id, row in df.iterrows():
    if pd.isna(row['new assigned box']):
        new_box_volume.append(None)
    else:
        new_box_volume.append(new_boxes_df.loc[row['new assigned box'],'box_volume'])
df.loc[:,'new box volume'] = new_box_volume

new_outlier_rate = calculate_outlier_rate(df, 'new assigned box')

#calculate new void fill rate 
new_void_fill_rate = (df.loc[:,'new box volume'] - df.loc[:,'volume'])/df.loc[:,'new box volume']
df.loc[:,'new void fill rate'] = new_void_fill_rate
new_weighted_avr_void_rate = calculate_weighted_void_rate(df, 'new void fill rate', 'new assigned box')

#calculate total new surface area
new_boxes_df.loc[:,'box_surface_area'] = 2 * (new_boxes_df.loc[:,'l']*new_boxes_df.loc[:,'w'] + new_boxes_df.loc[:,'l']*new_boxes_df.loc[:,'h'] + new_boxes_df.loc[:,'w']*new_boxes_df.loc[:,'h'])
df.loc[:,'new box surface area'] = df['new assigned box'].map(new_boxes_df['box_surface_area'])
new_surface_area= df.loc[:,'new box surface area'] * df.loc[:,'quantity']/1000000
df.loc[:,'new box surface area'] = new_surface_area
total_new_surface_area = df.loc[:,'new box surface area'].sum(skipna=True)

#calculate new void fill volume
total_new_void_vol_per_sku = (df['new box volume'] - df['volume']) * df['quantity']
is_packed_new = pd.notna(df['new assigned box'])
total_packed_qty_new = df.loc[is_packed_new, 'quantity'].sum()
average_new_void_volume = total_new_void_vol_per_sku.sum() / total_packed_qty_new

#dashboard
st.title('Order Data App')
st.subheader("Current Boxes VS New Boxes")
st.subheader("Outlier Rate and Weighted Average Void Fill Rate")

a, b= st.columns(2)
e, f= st.columns(2)

a.metric(label="Current Outlier Rate(%)", value=f"{outlier_rate:.2%}")
b.metric(label="Current Weighted Average Void Fill Rate", value=f"{weighted_avr_void_rate:.3f}")
e.metric(label="New Outlier Rate(%)", value=f"{new_outlier_rate:.2%}", delta=f"{(new_outlier_rate - outlier_rate):.2%}")
f.metric(label="New Weighted Average Void Fill Rate", value=f"{new_weighted_avr_void_rate:.3f}", delta=f"{(new_weighted_avr_void_rate - weighted_avr_void_rate):.2f}")

st.subheader("Total Surface Area and Average Void Fill Volume")
c, d= st.columns(2)
g, h= st.columns(2)
c.metric(label="Total Used Surface Area (m²)", value=f"{total_used_surface_area:.2f}")
d.metric(label="Average Current Void Fill Volume (Liters)", value=f"{average_current_void_volume:.2f}")
g.metric(label="Total New Surface Area (m²)", value=f"{total_new_surface_area:.2f}", delta=f"{(total_new_surface_area - total_used_surface_area):.2f}")
h.metric(label="Average New Void Fill Volume (Liters)", value=f"{average_new_void_volume:.2f}", delta=f"{(average_new_void_volume - average_current_void_volume):.2f}")


st.markdown('###  New Box')
st.write(new_boxes_df[['l', 'w', 'h','box_volume']])

#3D scatter plot
st.subheader(" 3D Scatter Plot")

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(df["dim_1"], df["dim_2"], df["dim_3"], s=15)

ax.set_xlabel("dim_1")
ax.set_ylabel("dim_2")
ax.set_zlabel("dim_3")
st.pyplot(fig)

#pie
st.subheader(" Proportion of products in different boxes ")
chart_choice = st.radio(
    "Select the Box Distribution to view:",
    options=[
        "Current Box Distribution Ratio (Old Box)",
        "New Box Distribution Ratio (New Box)"
    ],
    index=0, 
    horizontal=True 
)

box_summary_current = df.groupby('box')['quantity'].sum().reset_index()
box_summary_new = df.groupby('new assigned box')['quantity'].sum().reset_index()
if chart_choice == "Current Box Distribution Ratio (Old Box)":

    old_values = box_summary_current['quantity'] 
    old_labels = box_summary_current['box'].astype(str) 

    fig1, ax1 = plt.subplots(figsize=(5,5)) 
    ax1.pie(old_values, labels=old_labels, autopct="%1.1f%%", startangle=90)
    ax1.axis('equal')
    ax1.set_title("Current Box Distribution Ratio (Based on Quantity)")
    st.pyplot(fig1)
    plt.close(fig1)

elif chart_choice == "New Box Distribution Ratio (New Box)":
    
    new_values = box_summary_new['quantity'] 
    new_labels = box_summary_new['new assigned box'].astype(str)

    fig2, ax2 = plt.subplots(figsize=(6, 6)) 
    ax2.pie(new_values, labels=new_labels, autopct="%1.1f%%", startangle=90)
    ax2.axis('equal')
    ax2.set_title("New Box Distribution Ratio (Based on Quantity)")
    st.pyplot(fig2)
    plt.close(fig2)

#histograms
st.subheader(" Void Fill Rate Distribution Comparison")
hist_col1, hist_col2 = st.columns(2)
with hist_col1:
    
    fig_old, ax_old = plt.subplots(figsize=(6, 4)) 
    ax_old.hist(df["void fill rate"].dropna(), bins=30)
    ax_old.set_xlabel("Void Fill Rate")
    ax_old.set_ylabel("Frequency")
    ax_old.set_title("Current Box VFR")
    st.pyplot(fig_old)

with hist_col2:
    
    fig_new, ax_new = plt.subplots(figsize=(6, 4))
    ax_new.hist(df["new void fill rate"].dropna(), bins=30)
    ax_new.set_xlabel("New Void Fill Rate")
    ax_new.set_ylabel("Frequency")
    ax_new.set_title("New Box VFR")
    st.pyplot(fig_new)