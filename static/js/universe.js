import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- UI: INFO PANEL ---
const infoPanel = document.createElement('div');
infoPanel.id = 'info-panel';
infoPanel.style.cssText = `
    position: absolute; right: -400px; top: 0; width: 350px; height: 100%;
    background: rgba(8, 8, 15, 0.95); border-left: 2px solid #4facfe;
    padding: 40px 25px; color: #fff; transition: 0.5s cubic-bezier(0.77, 0, 0.175, 1);
    font-family: 'Segoe UI', sans-serif; overflow-y: auto; z-index: 1000;
    backdrop-filter: blur(10px); box-shadow: -10px 0 30px rgba(0,0,0,0.8);
`;
infoPanel.innerHTML = `
    <button id="close-btn" style="position:absolute; top:20px; right:20px; background:none; border:none; color:#4facfe; font-size:2.5rem; cursor:pointer;">&times;</button>
    <h1 id="panel-name" style="color:#4facfe; margin-top:10px; font-size: 2.2rem; text-transform: uppercase; letter-spacing: 2px;">Name</h1>
    <p id="panel-desc" style="line-height:1.8; color:#ccc; font-size: 1.1rem; margin-bottom: 30px;">Description...</p>
    <div style="height: 1px; background: linear-gradient(90deg, #4facfe, transparent); margin-bottom: 25px;"></div>
    <div id="panel-stats" style="display:grid; grid-template-columns:1fr; gap:15px;"></div>
`;
document.body.appendChild(infoPanel);
document.getElementById('close-btn').onclick = () => { infoPanel.style.right = '-400px'; };

// --- 1. SETUP SCENE ---
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x020205, 0.00002); 
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000000); 
const renderer = new THREE.WebGLRenderer({ antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.getElementById('canvas-container').appendChild(renderer.domElement);

// --- 2. LIGHTING ---
const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
scene.add(ambientLight);
const sunLight = new THREE.PointLight(0xffffff, 3.0, 0); 
scene.add(sunLight);

// --- 3. TEXTURE HELPERS ---
const textureLoader = new THREE.TextureLoader();

function getMaterial(path, color, isStar) {
    const matConfig = { color: color }; 
    const tex = textureLoader.load(path);
    if(isStar) return new THREE.MeshBasicMaterial({ map: tex, color: color });
    return new THREE.MeshStandardMaterial({ 
        map: tex, color: 0xffffff, roughness: 0.8, metalness: 0.2,
        emissive: color, emissiveIntensity: 0.15 
    });
}

function createSoftParticle() {
    const canvas = document.createElement('canvas');
    canvas.width = 64; canvas.height = 64;
    const ctx = canvas.getContext('2d');
    const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, 'rgba(255, 255, 255, 1)'); 
    grad.addColorStop(0.4, 'rgba(100, 100, 255, 0.2)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(canvas);
}
const dustTex = createSoftParticle();

// --- 4. ENVIRONMENT ---
function createStarField() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    const colors = [];
    const colorPalette = [new THREE.Color(0x9db4ff), new THREE.Color(0xffffff), new THREE.Color(0xffd2a1)];

    for (let i = 0; i < 2000; i++) {
        const x = (Math.random() - 0.5) * 15000;
        const y = (Math.random() - 0.5) * 15000;
        const z = (Math.random() - 0.5) * 15000;
        vertices.push(x, y, z);
        const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
        colors.push(color.r, color.g, color.b);
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({ size: 2, vertexColors: true, sizeAttenuation: false, transparent: true, opacity: 0.9 });
    scene.add(new THREE.Points(geometry, material));
}
createStarField();

function createNebulae() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < 200; i++) {
        const x = (Math.random() - 0.5) * 6000;
        const y = (Math.random() - 0.5) * 2000;
        const z = (Math.random() - 0.5) * 6000;
        vertices.push(x, y, z);
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({ size: 600, map: dustTex, color: 0x4400ff, transparent: true, opacity: 0.04, blending: THREE.AdditiveBlending, depthWrite: false });
    scene.add(new THREE.Points(geometry, material));
}
createNebulae();

// --- 5. CELESTIAL OBJECTS (DATA EXPANDED) ---
const celestialObjects = [
    { 
        name: "Sun", radius: 40, distance: 0, speed: 0, texture: '/static/textures/sun.jpg', type: 'star', color: 0xffaa00, 
        desc: "The star at the center of our Solar System. It contains 99.86% of the system's total mass.", 
        stats: { "Type": "Yellow Dwarf (G2V)", "Surface Temp": "5,500°C", "Core Temp": "15 Million °C", "Age": "4.6 Billion Years" } 
    },
    { 
        name: "Mercury", radius: 2, distance: 60, speed: 0.004, texture: '/static/textures/mercury.jpg', color: 0xaaaaaa, 
        desc: "The smallest planet in the Solar System and closest to the Sun. It has no atmosphere to retain heat.", 
        stats: { "Dist from Sun": "58 Million km", "Year": "88 Earth Days", "Day Length": "59 Earth Days", "Temp": "-180°C to 430°C", "Moons": "0" } 
    },
    { 
        name: "Venus", radius: 3.5, distance: 90, speed: 0.003, texture: '/static/textures/venus.jpg', color: 0xeecb8b, 
        desc: "The hottest planet due to a thick, toxic atmosphere that traps heat in a runaway greenhouse effect.", 
        stats: { "Dist from Sun": "108 Million km", "Year": "225 Earth Days", "Day Length": "243 Earth Days", "Temp": "465°C (Avg)", "Moons": "0" } 
    },
    { 
        name: "Earth", radius: 4, distance: 130, speed: 0.002, texture: '/static/textures/earth.jpg', type: 'earth', color: 0x2233ff, 
        desc: "Our home planet. The only known world with liquid water on the surface and life.", 
        stats: { "Dist from Sun": "150 Million km", "Year": "365.25 Days", "Day Length": "24 Hours", "Moons": "1 (The Moon)", "Avg Temp": "15°C" }, 
        satellites: [ { name: "The Moon", radius: 1.2, distance: 10, speed: 0.02, texture: '/static/textures/moon.jpg', color: 0xcccccc } ] 
    },
    { 
        name: "Mars", radius: 3, distance: 170, speed: 0.0018, texture: '/static/textures/mars.jpg', color: 0xff4500, 
        desc: "The Red Planet. It is a dusty, cold desert world with a very thin atmosphere.", 
        stats: { "Dist from Sun": "228 Million km", "Year": "687 Earth Days", "Day Length": "24h 37m", "Gravity": "3.72 m/s²", "Moons": "2 (Phobos, Deimos)" } 
    },
    { 
        name: "Jupiter", radius: 12, distance: 240, speed: 0.0008, texture: '/static/textures/jupiter.jpg', type: 'gas', color: 0xd9b38c, 
        desc: "The largest planet in the Solar System. A gas giant with a Great Red Spot storm larger than Earth.", 
        stats: { "Dist from Sun": "778 Million km", "Year": "12 Earth Years", "Day Length": "9h 56m", "Moons": "95 (Official)", "Type": "Gas Giant" } 
    },
    { 
        name: "Saturn", radius: 10, distance: 320, speed: 0.0006, texture: '/static/textures/saturn.jpg', type: 'saturn', color: 0xe4d5b6, 
        desc: "Adorned with a dazzling, complex system of icy rings. It is the least dense planet.", 
        stats: { "Dist from Sun": "1.4 Billion km", "Year": "29 Earth Years", "Day Length": "10h 42m", "Moons": "146 (Official)", "Rings": "7 Main Groups" } 
    },
    { 
        name: "Uranus", radius: 7, distance: 380, speed: 0.0004, texture: '/static/textures/uranus.jpg', type: 'gas', color: 0xadd8e6, 
        desc: "An ice giant that rotates on its side. It has a faint ring system and a pale blue color.", 
        stats: { "Dist from Sun": "2.9 Billion km", "Year": "84 Earth Years", "Day Length": "17h 14m", "Moons": "28", "Temp": "-224°C" } 
    },
    { 
        name: "Neptune", radius: 7, distance: 440, speed: 0.0002, texture: '/static/textures/neptune.jpg', type: 'gas', color: 0x00008b, 
        desc: "The most distant major planet. It is dark, cold, and whipped by supersonic winds.", 
        stats: { "Dist from Sun": "4.5 Billion km", "Year": "165 Earth Years", "Day Length": "16 Hours", "Moons": "16", "Wind Speed": "2,100 km/h" } 
    },
    { 
        name: "Alpha Centauri", radius: 30, distance: 0, xOffset: 3000, zOffset: 3000, speed: 0, texture: '/static/textures/sun.jpg', type: 'star', color: 0xffdd00, 
        desc: "The closest star system to the Solar System.", 
        stats: { "Distance": "4.37 Light Years", "Constellation": "Centaurus", "Type": "Triple Star System" } 
    },
    { 
        name: "Sirius", radius: 35, distance: 0, xOffset: -4000, zOffset: -2000, speed: 0, texture: '/static/textures/neptune.jpg', type: 'star', color: 0x8888ff, 
        desc: "The brightest star in Earth's night sky.", 
        stats: { "Distance": "8.6 Light Years", "Constellation": "Canis Major", "Luminosity": "25x Sun" } 
    },
    { 
        name: "Betelgeuse", radius: 80, distance: 0, xOffset: 3000, zOffset: -5000, speed: 0, texture: '/static/textures/mars.jpg', type: 'star', color: 0xff3300, 
        desc: "A massive Red Supergiant nearing the end of its life.", 
        stats: { "Distance": "640 Light Years", "Constellation": "Orion", "Radius": "887x Sun", "Fate": "Supernova" } 
    }
];

const meshList = []; 

function createObject(data) {
    const geometry = new THREE.SphereGeometry(data.radius, 64, 64);
    const material = getMaterial(data.texture, data.color, data.type === 'star');
    const mesh = new THREE.Mesh(geometry, material);

    if (data.type === 'star') {
        const glowGeo = new THREE.PlaneGeometry(data.radius * 12, data.radius * 12);
        const glowMat = new THREE.MeshBasicMaterial({ 
            map: dustTex, color: data.color, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false 
        });
        const glow = new THREE.Mesh(glowGeo, glowMat);
        glow.lookAt(camera.position); 
        mesh.add(glow);
        mesh.userData.glow = glow;
        mesh.add(new THREE.PointLight(data.color, 1.5, 1500));
    } 
    
    if (data.type === 'saturn') {
        const ringGeo = new THREE.RingGeometry(data.radius * 1.4, data.radius * 2.5, 64);
        const ringMat = new THREE.MeshStandardMaterial({ map: textureLoader.load('/static/textures/saturn_ring.png'), side: THREE.DoubleSide, transparent: true, opacity: 0.8, color: 0xcdc2b0 });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = -Math.PI / 2;
        mesh.add(ring);
    }

    const pivot = new THREE.Group();
    pivot.position.set(data.xOffset || 0, 0, data.zOffset || 0);
    scene.add(pivot);
    mesh.position.set(data.distance, 0, 0);
    pivot.add(mesh);
    
    mesh.userData = { name: data.name, desc: data.desc, stats: data.stats, pivot: pivot, speed: data.speed, radius: data.radius };
    meshList.push(mesh);

    if(data.distance > 0 && data.distance < 1000) {
        const lineGeo = new THREE.RingGeometry(data.distance - 0.2, data.distance + 0.2, 128);
        const lineMat = new THREE.MeshBasicMaterial({ 
            color: 0xffffff, side: THREE.DoubleSide, opacity: 0.15, transparent: true 
        });
        const line = new THREE.Mesh(lineGeo, lineMat);
        line.rotation.x = -Math.PI / 2;
        pivot.add(line);
    }

    if (data.satellites) {
        data.satellites.forEach(sat => {
            const satPivot = new THREE.Group();
            mesh.add(satPivot);
            const satMesh = new THREE.Mesh(new THREE.SphereGeometry(sat.radius, 32, 32), getMaterial(sat.texture, sat.color, false));
            satMesh.position.set(sat.distance, 0, 0);
            satPivot.add(satMesh);
            satMesh.userData = { isMoon: true, pivot: satPivot, speed: sat.speed, name: sat.name, desc: "A natural satellite.", stats: {"Orbiting": data.name} };
            meshList.push(satMesh);
        });
    }
}

celestialObjects.forEach(createObject);

// --- 6. ANIMATION & CONTROLS ---
const controls = new OrbitControls(camera, renderer.domElement);
camera.position.set(0, 100, 400);
controls.enableDamping = true;
controls.maxDistance = 10000; 

function animate() {
    requestAnimationFrame(animate);
    meshList.forEach(obj => {
        if(obj.userData.speed > 0 && obj.userData.pivot) obj.userData.pivot.rotation.y += obj.userData.speed;
        obj.rotation.y += 0.005;
        if(obj.userData.glow) obj.userData.glow.lookAt(camera.position);
        if(obj.userData.isMoon) obj.userData.pivot.rotation.y += obj.userData.speed;
    });
    controls.update();
    renderer.render(scene, camera);
}
animate();

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('click', (event) => {
    if (event.target.closest('#info-panel')) return;
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(meshList);
    if (intersects.length > 0) {
        const target = intersects[0].object;
        showInfo(target.userData);
        const dist = target.userData.radius * 4 || 20;
        const targetPos = new THREE.Vector3();
        target.getWorldPosition(targetPos);
        controls.target.copy(targetPos);
        camera.position.set(targetPos.x + dist, targetPos.y + 10, targetPos.z + dist);
    }
});

function showInfo(data) {
    document.getElementById('panel-name').innerText = data.name;
    document.getElementById('panel-desc').innerText = data.desc;
    const statsDiv = document.getElementById('panel-stats');
    statsDiv.innerHTML = "";
    if (data.stats) {
        for (const [key, value] of Object.entries(data.stats)) {
            statsDiv.innerHTML += `
                <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:8px;">
                    <div style="color:#888; font-size:0.85rem; margin-bottom:4px;">${key}</div>
                    <div style="color:#4facfe; font-weight:bold; font-size:1.1rem;">${value}</div>
                </div>`;
        }
    }
    infoPanel.style.right = '0px';
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});