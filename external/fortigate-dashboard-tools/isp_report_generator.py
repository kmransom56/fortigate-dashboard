#!/usr/bin/env python3
"""
ISP-Friendly Migration Report Generator
Creates a clean, professional report for ISP coordination
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os
import glob

def find_latest_migration_plan():
    """Find the most recent migration plan file"""
    pattern = "port2_migration_plan*.csv"
    files = glob.glob(pattern)
    
    if not files:
        print("Error: No migration plan files found!")
        print("Please run device_discovery_tool.py first to generate the migration plan.")
        return None
    
    # Sort by modification time, get most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Using migration plan: {latest_file}")
    return latest_file

def analyze_migration_data(df):
    """Analyze migration data for ISP report"""
    analysis = {}
    
    # Total device count
    analysis['total_devices'] = len(df)
    
    # Device type breakdown
    device_types = df['identified_type'].value_counts().to_dict()
    analysis['device_types'] = device_types
    
    # Vendor breakdown
    vendors = df['vendor'].value_counts().to_dict()
    analysis['vendors'] = vendors
    
    # Risk level breakdown
    risk_levels = df['migration_risk'].value_counts().to_dict()
    analysis['risk_levels'] = risk_levels
    
    # Responsive vs non-responsive
    if 'responsive' in df.columns:
        # Ensure responsive column is numeric
        if df['responsive'].dtype == 'object':
            # Try to convert to numeric, errors='coerce' will convert errors to NaN
            df['responsive'] = pd.to_numeric(df['responsive'], errors='coerce').fillna(0)
        
        responsive_count = df['responsive'].sum()
        analysis['responsive_devices'] = int(responsive_count)
    else:
        analysis['responsive_devices'] = 0
        
    analysis['non_responsive_devices'] = analysis['total_devices'] - analysis['responsive_devices']
    
    # Switch distribution
    if 'switch_name' in df.columns:
        switches = df['switch_name'].value_counts().to_dict()
        analysis['switches_affected'] = switches
        analysis['unique_switches'] = len(switches)
    
    return analysis

def create_isp_executive_summary(analysis):
    """Create executive summary for ISP"""
    summary = f"""
PORT 2 MIGRATION - EXECUTIVE SUMMARY
=====================================

MIGRATION OVERVIEW:
• Total devices requiring migration: {analysis['total_devices']:,}
• Unique FortiSwitches affected: {analysis.get('unique_switches', 'Unknown')}
• Migration priority: Pre-VLAN configuration change

DEVICE BREAKDOWN:
• Responsive devices: {analysis['responsive_devices']:,} ({analysis['responsive_devices']/analysis['total_devices']*100:.1f}%)
• Non-responsive devices: {analysis['non_responsive_devices']:,} ({analysis['non_responsive_devices']/analysis['total_devices']*100:.1f}%)

MIGRATION RISK ASSESSMENT:
"""
    
    for risk, count in analysis['risk_levels'].items():
        percentage = count / analysis['total_devices'] * 100
        summary += f"• {risk}: {count:,} devices ({percentage:.1f}%)\n"
    
    summary += f"""
COORDINATION REQUIREMENTS:
• ISP coordination needed BEFORE port 2 VLAN change
• Devices must be migrated to alternative ports first
• Migration window coordination required for high-risk devices
• Post-migration connectivity verification needed

TIMELINE:
• Low-risk migrations: Can proceed immediately  
• Medium-risk migrations: Require user coordination
• High-risk migrations: Require maintenance window scheduling
"""
    
    return summary

def create_device_summary_table(df):
    """Create a clean device summary table for ISP (no sensitive details)"""
    
    # Ensure responsive column is numeric
    df_copy = df.copy()
    if 'responsive' in df_copy.columns and df_copy['responsive'].dtype == 'object':
        df_copy['responsive'] = pd.to_numeric(df_copy['responsive'], errors='coerce').fillna(0)
    
    # Group devices by type and vendor for summary
    summary_data = []
    
    # Group by device type and vendor
    grouped = df_copy.groupby(['identified_type', 'vendor']).agg({
        'mac_address': 'count',
        'migration_risk': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'responsive': 'sum'
    }).reset_index()
    
    grouped.columns = ['Device_Type', 'Vendor', 'Device_Count', 'Primary_Risk_Level', 'Responsive_Count']
    
    # Calculate percentages
    grouped['Responsive_Percentage'] = (grouped['Responsive_Count'] / grouped['Device_Count'] * 100).round(1)
    
    # Sort by device count (most devices first)
    grouped = grouped.sort_values('Device_Count', ascending=False)
    
    return grouped

def create_switch_impact_summary(df):
    """Create switch impact summary"""
    if 'switch_name' not in df.columns:
        return pd.DataFrame()
    
    # Ensure responsive column is numeric
    df_copy = df.copy()
    if 'responsive' in df_copy.columns and df_copy['responsive'].dtype == 'object':
        df_copy['responsive'] = pd.to_numeric(df_copy['responsive'], errors='coerce').fillna(0)
    
    switch_summary = df_copy.groupby('switch_name').agg({
        'mac_address': 'count',
        'migration_risk': lambda x: ', '.join(str(item) for item in x.value_counts().head(3).index.tolist()),
        'responsive': 'sum',
        'identified_type': lambda x: ', '.join(str(item) for item in x.value_counts().head(3).index.tolist())
    }).reset_index()
    
    switch_summary.columns = ['Switch_Name', 'Devices_on_Port2', 'Primary_Risk_Levels', 'Responsive_Devices', 'Primary_Device_Types']
    switch_summary = switch_summary.sort_values('Devices_on_Port2', ascending=False)
    
    return switch_summary

def generate_migration_timeline(analysis):
    """Generate suggested migration timeline"""
    
    timeline = []
    current_date = datetime.now()
    
    # Low risk - can start immediately
    low_risk = sum(count for risk, count in analysis['risk_levels'].items() if 'LOW' in risk)
    if low_risk > 0:
        timeline.append({
            'Phase': 'Phase 1 - Low Risk',
            'Start_Date': current_date.strftime('%Y-%m-%d'),
            'Duration': '1-2 business days',
            'Device_Count': low_risk,
            'Description': 'Non-responsive and low-impact devices'
        })
    
    # Medium risk - coordination needed
    medium_risk = sum(count for risk, count in analysis['risk_levels'].items() if 'MEDIUM' in risk)
    if medium_risk > 0:
        start_date = current_date + timedelta(days=3)
        timeline.append({
            'Phase': 'Phase 2 - Medium Risk',
            'Start_Date': start_date.strftime('%Y-%m-%d'),
            'Duration': '3-5 business days',
            'Device_Count': medium_risk,
            'Description': 'Active devices requiring user coordination'
        })
    
    # High risk - maintenance window
    high_risk = sum(count for risk, count in analysis['risk_levels'].items() if 'HIGH' in risk)
    if high_risk > 0:
        start_date = current_date + timedelta(days=7)
        timeline.append({
            'Phase': 'Phase 3 - High Risk',
            'Start_Date': start_date.strftime('%Y-%m-%d'),
            'Duration': 'Scheduled maintenance window',
            'Device_Count': high_risk,
            'Description': 'Critical infrastructure requiring downtime'
        })
    
    return pd.DataFrame(timeline)

def create_isp_report():
    """Generate complete ISP report"""
    
    # Find latest migration plan
    migration_file = find_latest_migration_plan()
    if not migration_file:
        return
    
    # Load data
    try:
        df = pd.read_csv(migration_file)
        print(f"Loaded {len(df)} devices from migration plan")
    except Exception as e:
        print(f"Error loading migration plan: {e}")
        return
    
    # Analyze data
    analysis = analyze_migration_data(df)
    
    # Generate timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create executive summary
    exec_summary = create_isp_executive_summary(analysis)
    
    # Create device summary table
    device_summary = create_device_summary_table(df)
    
    # Create switch impact summary  
    switch_summary = create_switch_impact_summary(df)
    
    # Create migration timeline
    timeline = generate_migration_timeline(analysis)
    
    # Save executive summary as text file
    summary_filename = f"ISP_Migration_Summary_{timestamp}.txt"
    with open(summary_filename, 'w') as f:
        f.write(exec_summary)
        f.write(f"\n\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        f.write(f"\nSource data: {migration_file}")
        f.write(f"\nTotal devices analyzed: {len(df):,}")
    
    # Save device summary as CSV
    device_csv = f"ISP_Device_Summary_{timestamp}.csv"
    device_summary.to_csv(device_csv, index=False)
    
    # Save switch impact summary
    if not switch_summary.empty:
        switch_csv = f"ISP_Switch_Impact_{timestamp}.csv"
        switch_summary.to_csv(switch_csv, index=False)
    
    # Save migration timeline
    timeline_csv = f"ISP_Migration_Timeline_{timestamp}.csv"
    timeline.to_csv(timeline_csv, index=False)
    
    # Create comprehensive Excel report
    excel_filename = f"ISP_Migration_Report_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Executive summary as first sheet
        summary_df = pd.DataFrame([exec_summary], columns=['Executive_Summary'])
        summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
        
        # Device summary
        device_summary.to_excel(writer, sheet_name='Device_Summary', index=False)
        
        # Switch impact
        if not switch_summary.empty:
            switch_summary.to_excel(writer, sheet_name='Switch_Impact', index=False)
        
        # Migration timeline
        timeline.to_excel(writer, sheet_name='Migration_Timeline', index=False)
    
    # Print results
    print(f"\n🎯 ISP REPORT GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📄 Executive Summary: {summary_filename}")
    print(f"📊 Device Summary: {device_csv}")
    if not switch_summary.empty:
        print(f"🔀 Switch Impact: {switch_csv}")
    print(f"📅 Migration Timeline: {timeline_csv}")
    print(f"📑 Complete Excel Report: {excel_filename}")
    print("=" * 60)
    
    print(f"\n📧 SEND TO ISP:")
    print(f"   Primary: {excel_filename}")
    print(f"   Backup: {summary_filename}")
    
    print(f"\n💡 KEY POINTS FOR ISP COORDINATION:")
    print(f"   • {analysis['total_devices']:,} devices need migration BEFORE VLAN change")
    print(f"   • {analysis.get('unique_switches', 'Multiple')} FortiSwitches affected")
    print(f"   • {analysis['responsive_devices']:,} active devices need coordination")
    
    # Show quick stats
    print(f"\n📈 QUICK STATS:")
    print(f"   • Responsive devices: {analysis['responsive_devices']:,}")
    print(f"   • Non-responsive: {analysis['non_responsive_devices']:,}")
    
    for risk, count in analysis['risk_levels'].items():
        print(f"   • {risk}: {count:,}")

def preview_report():
    """Preview what will be in the ISP report"""
    migration_file = find_latest_migration_plan()
    if not migration_file:
        return
    
    df = pd.read_csv(migration_file)
    analysis = analyze_migration_data(df)
    
    print("ISP REPORT PREVIEW")
    print("=" * 50)
    print(f"Total devices: {analysis['total_devices']:,}")
    print(f"Unique switches: {analysis.get('unique_switches', 'Unknown')}")
    print(f"Active devices: {analysis['responsive_devices']:,}")
    
    print(f"\nTop 5 device types:")
    for device_type, count in list(analysis['device_types'].items())[:5]:
        print(f"  • {device_type}: {count:,}")
    
    print(f"\nRisk breakdown:")
    for risk, count in analysis['risk_levels'].items():
        percentage = count / analysis['total_devices'] * 100
        print(f"  • {risk}: {count:,} ({percentage:.1f}%)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "preview":
            preview_report()
        elif command == "help":
            print("Usage:")
            print(f"  {sys.argv[0]}         # Generate ISP report")
            print(f"  {sys.argv[0]} preview # Preview report contents")
            print(f"  {sys.argv[0]} help    # Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for usage information")
    else:
        create_isp_report()
