#!/bin/bash
# Test script to verify all FortiGate Dashboard links

BASE_URL="http://127.0.0.1:8001"
echo "Testing FortiGate Dashboard links on $BASE_URL"
echo "================================================"
echo ""

# Test main pages
echo "=== Main Pages ==="
for route in "/" "/topology-fortigate" "/topology" "/topology-3d" "/switches" "/enterprise" "/dashboard" "/icons"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${route}")
    if [ "$status" = "200" ]; then
        echo "✓ $route - OK ($status)"
    else
        echo "✗ $route - FAILED ($status)"
    fi
done

echo ""
echo "=== API Endpoints ==="
# Test API endpoints
for route in "/api/topology_data" "/api/scraped_topology" "/api/topology_3d_data" "/api/cloud_status" "/api/eraser/status"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${route}")
    if [ "$status" = "200" ]; then
        echo "✓ $route - OK ($status)"
    else
        echo "✗ $route - FAILED ($status)"
    fi
done

echo ""
echo "=== Static Files ==="
# Test static file access
for route in "/static/vendor/3d-force-graph.min.js" "/static/js/3d-device-models.js"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${route}")
    if [ "$status" = "200" ]; then
        echo "✓ $route - OK ($status)"
    else
        echo "✗ $route - FAILED ($status)"
    fi
done

echo ""
echo "=== Summary ==="
echo "Test completed. Check results above."

