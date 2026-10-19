#!/usr/bin/env bash
# Run inside dell-rack-sim. The large download stays on the VM's persistent disk.
set -euo pipefail
cd /workspace
mkdir -p assets/vendor
if [ ! -f assets/vendor/datacenter.zip ]; then
  curl --fail --location --retry 3 --continue-at - \
    'https://d4i3qtqj3r0z5.cloudfront.net/Datacenter_NVD%4010012.zip' \
    -o assets/vendor/datacenter.zip.part
  test "$(stat -c %s assets/vendor/datacenter.zip.part)" = 9836277726
  mv assets/vendor/datacenter.zip.part assets/vendor/datacenter.zip
fi
sha256sum --check <<< '4972d1a9726b36279d7c26531b4d0a084156b7d512f5340b6e1063a9cf458fd4  assets/vendor/datacenter.zip'
if [ ! -f assets/vendor/datacenter/Assets/DigitalTwin/Assets/Datacenter/Racks/Rack_42U_A/Rack_42U_A_01.usd ]; then
  python3 scripts/catalog_datacenter.py
fi
