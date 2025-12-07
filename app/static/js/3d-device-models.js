/**
 * 3D Device Model Generator
 * Creates realistic 3D representations of network devices
 */

// Color palette matching FortiGate branding
const DEVICE_COLORS = {
  fortigate: {
    body: 0xe8e8e8,
    accent: 0xc41e3a,
    port: 0x1a1a1a
  },
  fortiswitch: {
    body: 0xd0d0d0,
    accent: 0xc41e3a,
    port: 0x2a2a2a
  },
  laptop: {
    body: 0xa8a8a8,
    screen: 0x1a1a1a,
    keyboard: 0x2a2a2a
  },
  wireless: {
    body: 0xf5f5f5,
    led: 0x00ff00
  }
};

/**
 * Create a 3D FortiGate firewall model
 */
function createFortiGateModel(size = 10) {
  const group = new THREE.Group();

  // Main body - rectangular hardware unit
  const bodyGeom = new THREE.BoxGeometry(size * 1.5, size * 0.4, size * 0.8);
  const bodyMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortigate.body,
    shininess: 60,
    specular: 0x222222
  });
  const body = new THREE.Mesh(bodyGeom, bodyMat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // Front panel with FORTIGATE branding
  const panelGeom = new THREE.BoxGeometry(size * 1.48, size * 0.35, size * 0.1);
  const panelMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortigate.accent,
    shininess: 80
  });
  const panel = new THREE.Mesh(panelGeom, panelMat);
  panel.position.z = size * 0.45;
  panel.position.y = size * 0.02;
  group.add(panel);

  // Ethernet ports (4 ports)
  const portGeom = new THREE.BoxGeometry(size * 0.15, size * 0.12, size * 0.08);
  const portMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortigate.port
  });

  for (let i = 0; i < 4; i++) {
    const port = new THREE.Mesh(portGeom, portMat);
    port.position.x = -size * 0.5 + i * size * 0.35;
    port.position.z = size * 0.48;
    port.position.y = -size * 0.1;
    group.add(port);
  }

  // LED indicators
  const ledGeom = new THREE.CircleGeometry(size * 0.03, 8);
  const ledMat = new THREE.MeshBasicMaterial({
    color: 0x00ff00,
    emissive: 0x00ff00,
    emissiveIntensity: 0.5
  });

  for (let i = 0; i < 3; i++) {
    const led = new THREE.Mesh(ledGeom, ledMat);
    led.position.x = size * 0.3 + i * size * 0.15;
    led.position.y = size * 0.15;
    led.position.z = size * 0.41;
    led.rotation.y = 0;
    group.add(led);
  }

  // Ventilation slots on sides
  const slotGeom = new THREE.PlaneGeometry(size * 0.05, size * 0.25);
  const slotMat = new THREE.MeshBasicMaterial({
    color: 0x1a1a1a,
    side: THREE.DoubleSide
  });

  for (let i = 0; i < 6; i++) {
    const slot = new THREE.Mesh(slotGeom, slotMat);
    slot.position.x = size * 0.75;
    slot.position.z = -size * 0.3 + i * size * 0.12;
    slot.rotation.y = Math.PI / 2;
    group.add(slot);
  }

  return group;
}

/**
 * Create a 3D FortiSwitch model
 */
function createFortiSwitchModel(size = 10) {
  const group = new THREE.Group();

  // Main switch body
  const bodyGeom = new THREE.BoxGeometry(size * 1.6, size * 0.3, size * 0.7);
  const bodyMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortiswitch.body,
    shininess: 50
  });
  const body = new THREE.Mesh(bodyGeom, bodyMat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // Front panel
  const panelGeom = new THREE.BoxGeometry(size * 1.58, size * 0.28, size * 0.08);
  const panelMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortiswitch.accent,
    shininess: 70
  });
  const panel = new THREE.Mesh(panelGeom, panelMat);
  panel.position.z = size * 0.39;
  group.add(panel);

  // Ethernet ports array (8 ports)
  const portGeom = new THREE.BoxGeometry(size * 0.12, size * 0.1, size * 0.06);
  const portMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.fortiswitch.port
  });

  for (let i = 0; i < 8; i++) {
    const port = new THREE.Mesh(portGeom, portMat);
    port.position.x = -size * 0.65 + i * size * 0.19;
    port.position.z = size * 0.42;
    port.position.y = -size * 0.05;
    group.add(port);

    // Port LED
    const ledGeom = new THREE.CircleGeometry(size * 0.02, 6);
    const ledColor = i % 2 === 0 ? 0x00ff00 : 0xffaa00;
    const ledMat = new THREE.MeshBasicMaterial({
      color: ledColor,
      emissive: ledColor,
      emissiveIntensity: 0.3
    });
    const led = new THREE.Mesh(ledGeom, ledMat);
    led.position.x = port.position.x;
    led.position.y = size * 0.08;
    led.position.z = size * 0.36;
    group.add(led);
  }

  return group;
}

/**
 * Create a 3D laptop/endpoint model
 */
function createLaptopModel(size = 8) {
  const group = new THREE.Group();

  // Laptop base (keyboard section)
  const baseGeom = new THREE.BoxGeometry(size * 0.8, size * 0.05, size * 0.6);
  const baseMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.laptop.body,
    shininess: 40
  });
  const base = new THREE.Mesh(baseGeom, baseMat);
  base.position.y = -size * 0.2;
  base.rotation.x = Math.PI * 0.05;
  base.castShadow = true;
  base.receiveShadow = true;
  group.add(base);

  // Keyboard texture
  const keyboardGeom = new THREE.PlaneGeometry(size * 0.7, size * 0.5);
  const keyboardMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.laptop.keyboard,
    shininess: 10
  });
  const keyboard = new THREE.Mesh(keyboardGeom, keyboardMat);
  keyboard.position.y = -size * 0.17;
  keyboard.position.z = size * 0.02;
  keyboard.rotation.x = -Math.PI * 0.45;
  group.add(keyboard);

  // Screen
  const screenGeom = new THREE.BoxGeometry(size * 0.8, size * 0.6, size * 0.04);
  const screenMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.laptop.body,
    shininess: 50
  });
  const screen = new THREE.Mesh(screenGeom, screenMat);
  screen.position.y = size * 0.1;
  screen.position.z = -size * 0.25;
  screen.rotation.x = Math.PI * 0.15;
  screen.castShadow = true;
  group.add(screen);

  // Screen display (dark)
  const displayGeom = new THREE.PlaneGeometry(size * 0.75, size * 0.55);
  const displayMat = new THREE.MeshBasicMaterial({
    color: DEVICE_COLORS.laptop.screen,
    emissive: 0x0a0a0a,
    emissiveIntensity: 0.2
  });
  const display = new THREE.Mesh(displayGeom, displayMat);
  display.position.y = size * 0.1;
  display.position.z = -size * 0.23;
  display.rotation.x = Math.PI * 0.15;
  group.add(display);

  return group;
}

/**
 * Create a 3D wireless access point model
 */
function createWirelessAPModel(size = 8) {
  const group = new THREE.Group();

  // Main AP body (rounded square)
  const bodyGeom = new THREE.CylinderGeometry(size * 0.5, size * 0.5, size * 0.15, 32);
  const bodyMat = new THREE.MeshPhongMaterial({
    color: DEVICE_COLORS.wireless.body,
    shininess: 80,
    specular: 0x333333
  });
  const body = new THREE.Mesh(bodyGeom, bodyMat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // LED ring indicator
  const ringGeom = new THREE.TorusGeometry(size * 0.15, size * 0.02, 8, 24);
  const ringMat = new THREE.MeshBasicMaterial({
    color: DEVICE_COLORS.wireless.led,
    emissive: DEVICE_COLORS.wireless.led,
    emissiveIntensity: 0.5
  });
  const ring = new THREE.Mesh(ringGeom, ringMat);
  ring.position.y = size * 0.08;
  ring.rotation.x = Math.PI / 2;
  group.add(ring);

  // Central logo area
  const logoGeom = new THREE.CircleGeometry(size * 0.12, 16);
  const logoMat = new THREE.MeshPhongMaterial({
    color: 0xc41e3a,
    shininess: 60
  });
  const logo = new THREE.Mesh(logoGeom, logoMat);
  logo.position.y = size * 0.076;
  logo.rotation.x = -Math.PI / 2;
  group.add(logo);

  // Antenna (small protrusion on side)
  const antennaGeom = new THREE.CylinderGeometry(size * 0.02, size * 0.02, size * 0.3, 8);
  const antennaMat = new THREE.MeshPhongMaterial({
    color: 0x2a2a2a,
    shininess: 30
  });
  const antenna = new THREE.Mesh(antennaGeom, antennaMat);
  antenna.position.x = size * 0.4;
  antenna.position.y = size * 0.1;
  antenna.rotation.z = Math.PI * 0.25;
  group.add(antenna);

  return group;
}

/**
 * Create a 3D wireless device (phone/tablet)
 */
function createWirelessDeviceModel(size = 6) {
  const group = new THREE.Group();

  // Device body (smartphone/tablet shape)
  const bodyGeom = new THREE.BoxGeometry(size * 0.4, size * 0.7, size * 0.08);
  const bodyMat = new THREE.MeshPhongMaterial({
    color: 0x1a1a1a,
    shininess: 70,
    specular: 0x444444
  });
  const body = new THREE.Mesh(bodyGeom, bodyMat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // Screen
  const screenGeom = new THREE.PlaneGeometry(size * 0.35, size * 0.62);
  const screenMat = new THREE.MeshBasicMaterial({
    color: 0x0a0a0a,
    emissive: 0x1a3a4a,
    emissiveIntensity: 0.3
  });
  const screen = new THREE.Mesh(screenGeom, screenMat);
  screen.position.z = size * 0.041;
  group.add(screen);

  // Camera
  const cameraGeom = new THREE.CircleGeometry(size * 0.03, 12);
  const cameraMat = new THREE.MeshBasicMaterial({
    color: 0x000000
  });
  const camera = new THREE.Mesh(cameraGeom, cameraMat);
  camera.position.y = size * 0.3;
  camera.position.z = size * 0.041;
  group.add(camera);

  return group;
}

/**
 * Main function to create appropriate 3D model based on device type
 */
function create3DDeviceModel(deviceType, size = 10) {
  switch (deviceType.toLowerCase()) {
    case 'fortigate':
      return createFortiGateModel(size);
    case 'fortiswitch':
      return createFortiSwitchModel(size);
    case 'laptop':
    case 'endpoint':
    case 'server':
      return createLaptopModel(size);
    case 'wireless':
    case 'access_point':
    case 'ap':
      return createWirelessAPModel(size);
    case 'wireless_device':
    case 'mobile':
    case 'tablet':
      return createWirelessDeviceModel(size);
    default:
      // Generic fallback - simple box
      const fallbackGeom = new THREE.BoxGeometry(size * 0.6, size * 0.4, size * 0.3);
      const fallbackMat = new THREE.MeshPhongMaterial({
        color: 0x6b7280,
        shininess: 50
      });
      return new THREE.Mesh(fallbackGeom, fallbackMat);
  }
}

// Export for use in topology_3d.html
window.create3DDeviceModel = create3DDeviceModel;
