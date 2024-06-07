#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 11:21:50 2024

@author: ssalie
"""
import os
import json
import sys

def extract_data(file_path):
    # Extract the filename from the path
    file_name = os.path.basename(file_path)
    # Create a dictionary with the filename
    output = {"filename": file_name,
              "vendor_name":"None",
              "vendor_invoice_id":"None",
              "invoice_date":"None",
              "vendor_tax_id":"None",
              "vendor_registration_number":"None",
              "purchase_order_number":"None",
              "bank_name":"None",
              "bank_account_number":"None",
              "bank_branch_code":"None",
              "bank_sort_code":"None",
              "account_holder_name":"None",
              "net_amount":"None",
              "total_amount":"None",
              "tax_amount":"None",
              "address":"None",
              "object_id":"None",
              "extraction_time":"None"}
    # Return the JSON output
    return json.dumps(output)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pdf_extractor.py <file_path>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        result = extract_data(file_path)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
