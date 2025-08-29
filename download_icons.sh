#!/bin/bash

echo "🔍 Enhanced Icon Download Script"
echo "================================"

# Create downloads directory
DOWNLOAD_DIR="downloaded_files"
mkdir -p "$DOWNLOAD_DIR"
echo "📁 Using directory: $DOWNLOAD_DIR"

# Counter for downloads
TOTAL_DOWNLOADED=0

# Function to download a file
download_icon() {
    local url="$1"
    local filename="$2"
    local filepath="$DOWNLOAD_DIR/$filename"
    
    if [[ -f "$filepath" ]]; then
        echo "⏭️  Skipping (exists): $filename"
        return 0
    fi
    
    echo "⬇️  Downloading: $filename"
    if curl -L -s -o "$filepath" "$url" --connect-timeout 10 --max-time 30; then
        local size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "unknown")
        echo "✅ Saved: $filename ($size bytes)"
        ((TOTAL_DOWNLOADED++))
        return 0
    else
        echo "❌ Failed: $filename"
        rm -f "$filepath" 2>/dev/null
        return 1
    fi
}

echo ""
echo "📚 Downloading from Simple Icons..."
# Simple Icons - Network vendors
simple_icons_base="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons"
simple_icons=(
    "fortinet"
    "cisco" 
    "ubiquiti"
    "mikrotik"
    "pfsense"
    "openwrt"
    "ddwrt"
    "meraki"
    "juniper"
    "aruba"
    "dell"
    "hp"
    "lenovo"
    "supermicro"
)

for icon in "${simple_icons[@]}"; do
    download_icon "$simple_icons_base/$icon.svg" "simple_$icon.svg"
    sleep 0.2
done

echo ""
echo "🪶 Downloading from Feather Icons..."
# Feather Icons - General tech icons
feather_base="https://raw.githubusercontent.com/feathericons/feather/master/icons"
feather_icons=(
    "wifi"
    "server"
    "monitor"
    "smartphone"
    "tablet"
    "laptop"
    "shield"
    "lock"
    "unlock"
    "settings"
    "activity"
    "bar-chart"
    "trending-up"
)

for icon in "${feather_icons[@]}"; do
    download_icon "$feather_base/$icon.svg" "feather_$icon.svg"
    sleep 0.2
done

echo ""
echo "🏪 Downloading POS/Retail specific icons..."
# Microsoft Fluent UI - POS icons
fluent_icons=(
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Cash%20Register/SVG/ic_fluent_cash_register_24_regular.svg:fluent_cash_register.svg"
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Point%20Of%20Sale/SVG/ic_fluent_point_of_sale_24_regular.svg:fluent_point_of_sale.svg"
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Food/SVG/ic_fluent_food_24_regular.svg:fluent_food.svg"
)

for icon_info in "${fluent_icons[@]}"; do
    IFS=':' read -r url filename <<< "$icon_info"
    download_icon "$url" "$filename"
    sleep 0.2
done

echo ""
echo "🎯 Downloading additional useful icons..."
# Additional useful icons
additional_icons=(
    "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/device-desktop.svg:tabler_desktop.svg"
    "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/router.svg:tabler_router.svg"
    "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/device-mobile.svg:tabler_mobile.svg"
    "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/cash.svg:tabler_cash.svg"
    "https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/shopping-cart.svg:tabler_cart.svg"
)

for icon_info in "${additional_icons[@]}"; do
    IFS=':' read -r url filename <<< "$icon_info"
    download_icon "$url" "$filename"
    sleep 0.2
done

echo ""
echo "🎉 Download Complete!"
echo "📊 Total icons downloaded this session: $TOTAL_DOWNLOADED"
echo ""
echo "📁 Contents of $DOWNLOAD_DIR:"
ls -la "$DOWNLOAD_DIR" | grep -E '\.(svg|png|ico)$' | while read -r line; do
    filename=$(echo "$line" | awk '{print $9}')
    size=$(echo "$line" | awk '{print $5}')
    echo "  📄 $filename ($size bytes)"
done

echo ""
echo "✨ All done! Icons are ready for your FortiGate dashboard."

