# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 16:24:02 2025

@author: swan_
"""
import pandas as pd
import math
class Box:
    def __init__(self, length, width, height, box_id=None):
        self.l = length
        self.w = width
        self.h = height
        self.box_id = box_id

    def volume(self):
        return self.l * self.w * self.h / 1000000.0  
    
#check if fits 
    def fits(self, item_l, item_w, item_h):
        box_dims = sorted([self.l, self.w, self.h], reverse=True)
        return item_l <= box_dims[0] and item_w <= box_dims[1] and item_h <= box_dims[2]
    
def assign_boxes(items_df, box_list, return_index=False):
    assigned_results = []
    for sku_id, row in items_df.iterrows():
        found_box = False
        for i, box in enumerate(box_list):
            if box.fits(row['dim_1'], row['dim_2'], row['dim_3']):
                found_box = True
                if return_index:
                    assigned_results.append(i) 
                else:
                    assigned_results.append(box.box_id) 
                break            
        if not found_box:
            assigned_results.append(None)
    return assigned_results

def calculate_outlier_rate(df, box_col_name):
    outlier_quan = []
    for sku_id, row in df.iterrows():
        if pd.isna(row[box_col_name]):
            outlier_quan.append(row['quantity'])    
    total_quantity = sum(df.loc[:, 'quantity'])   
    if total_quantity == 0:
        return 0.0        
    return sum(outlier_quan) / total_quantity

def calculate_weighted_void_rate(df, void_rate_col_name, box_col_name):
    is_packed = pd.notna(df[box_col_name])
    fitted_quantity = df.loc[is_packed, 'quantity'].sum()    
    if fitted_quantity == 0:
        return 0.0
    weighted_avr_void_rate_df = df.loc[is_packed, 'quantity'] * df.loc[is_packed, void_rate_col_name] / fitted_quantity   
    return weighted_avr_void_rate_df.sum()

