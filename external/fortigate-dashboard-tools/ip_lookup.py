#!/usr/bin/env python3
"""
IP to Hostname Lookup Script
Performs reverse DNS lookups for a list of IP addresses
"""

import socket
import concurrent.futures
import csv
import sys
from typing import List, Tuple, Optional
import time

def reverse_dns_lookup(ip_address: str, timeout: int = 5) -> Tuple[str, Optional[str], str]:
    """
    Perform reverse DNS lookup for a single IP address
    
    Args:
        ip_address: IP address to lookup
        timeout: Timeout in seconds for the lookup
        
    Returns:
        Tuple of (ip_address, hostname, status)
    """
    try:
        # Set socket timeout
        socket.setdefaulttimeout(timeout)
        
        # Perform reverse DNS lookup
        hostname = socket.gethostbyaddr(ip_address)[0]
        return ip_address, hostname, "SUCCESS"
        
    except socket.herror:
        return ip_address, None, "NO_HOSTNAME"
    except socket.gaierror:
        return ip_address, None, "DNS_ERROR"
    except socket.timeout:
        return ip_address, None, "TIMEOUT"
    except Exception as e:
        return ip_address, None, f"ERROR: {str(e)}"

def bulk_reverse_dns_lookup(ip_list: List[str], 
                           max_workers: int = 10, 
                           timeout: int = 5) -> List[Tuple[str, Optional[str], str]]:
    """
    Perform reverse DNS lookups for multiple IP addresses in parallel
    
    Args:
        ip_list: List of IP addresses to lookup
        max_workers: Maximum number of concurrent threads
        timeout: Timeout in seconds for each lookup
        
    Returns:
        List of tuples (ip_address, hostname, status)
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all lookup tasks
        future_to_ip = {
            executor.submit(reverse_dns_lookup, ip, timeout): ip 
            for ip in ip_list
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_ip):
            results.append(future.result())
    
    return results

def read_ips_from_file(filename: str) -> List[str]:
    """Read IP addresses from a text file (one per line)"""
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return []

def save_results_to_csv(results: List[Tuple[str, Optional[str], str]], filename: str):
    """Save results to CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['IP_Address', 'Hostname', 'Status'])
        
        for ip, hostname, status in results:
            writer.writerow([ip, hostname or 'N/A', status])

def print_results(results: List[Tuple[str, Optional[str], str]]):
    """Print results in a formatted table"""
    print(f"\n{'IP Address':<15} {'Hostname':<50} {'Status':<15}")
    print("-" * 80)
    
    for ip, hostname, status in results:
        hostname_display = hostname or 'N/A'
        print(f"{ip:<15} {hostname_display:<50} {status:<15}")

def main():
    """Main function with different usage examples"""
    
    # Example 1: Manual list of IP addresses
    ip_addresses = [
        "8.8.8.8",
        "1.1.1.1", 
        "208.67.222.222",
        "192.168.1.1",
        "127.0.0.1"
    ]
    
    print("Performing reverse DNS lookups...")
    start_time = time.time()
    
    # Perform lookups
    results = bulk_reverse_dns_lookup(ip_addresses, max_workers=5, timeout=3)
    
    # Sort results by IP address for consistent output
    results.sort(key=lambda x: socket.inet_aton(x[0]))
    
    end_time = time.time()
    
    # Display results
    print_results(results)
    print(f"\nCompleted {len(results)} lookups in {end_time - start_time:.2f} seconds")
    
    # Save to CSV
    save_results_to_csv(results, 'dns_lookup_results.csv')
    print("Results saved to 'dns_lookup_results.csv'")

def lookup_from_file(filename: str, output_file: str = None):
    """
    Read IP addresses from file and perform lookups
    
    Usage example:
    lookup_from_file('ip_list.txt', 'output_results.csv')
    """
    ip_list = read_ips_from_file(filename)
    if not ip_list:
        return
    
    print(f"Loaded {len(ip_list)} IP addresses from {filename}")
    
    results = bulk_reverse_dns_lookup(ip_list, max_workers=10, timeout=5)
    results.sort(key=lambda x: socket.inet_aton(x[0]))
    
    print_results(results)
    
    if output_file:
        save_results_to_csv(results, output_file)
        print(f"Results saved to '{output_file}'")

# Additional utility functions for automation workflows

def get_successful_lookups(results: List[Tuple[str, Optional[str], str]]) -> List[Tuple[str, str]]:
    """Filter results to only successful lookups"""
    return [(ip, hostname) for ip, hostname, status in results if status == "SUCCESS"]

def get_failed_lookups(results: List[Tuple[str, Optional[str], str]]) -> List[str]:
    """Get list of IP addresses that failed lookup"""
    return [ip for ip, hostname, status in results if status != "SUCCESS"]

def generate_hosts_file_entries(results: List[Tuple[str, Optional[str], str]]) -> str:
    """Generate hosts file format entries from successful lookups"""
    entries = []
    for ip, hostname, status in results:
        if status == "SUCCESS" and hostname:
            entries.append(f"{ip}\t{hostname}")
    return "\n".join(entries)

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'dns_results.csv'
        lookup_from_file(input_file, output_file)
    else:
        main()