import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { Evaluation, Project } from '../types'

type ViewName = 'iso' | 'side' | 'bow' | 'top'

type Props = {
  project: Project
  evaluation: Evaluation
}

function numberValue(value: unknown, fallback = 0): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function textSprite(text: string, color: string): THREE.Sprite {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 96
  const context = canvas.getContext('2d')
  if (context) {
    context.clearRect(0, 0, canvas.width, canvas.height)
    context.fillStyle = 'rgba(3, 17, 24, .82)'
    context.roundRect(4, 4, 248, 80, 14)
    context.fill()
    context.font = '600 34px system-ui'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillStyle = color
    context.fillText(text, 128, 45)
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true }))
  sprite.scale.set(1.35, 0.5, 1)
  sprite.userData.texture = texture
  return sprite
}

export function HullScene({ project, evaluation }: Props) {
  const mountRef = useRef<HTMLDivElement>(null)
  const viewHandlerRef = useRef<(view: ViewName) => void>(() => undefined)
  const [activeView, setActiveView] = useState<ViewName>('iso')

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#03151f')
    scene.fog = new THREE.Fog('#03151f', 12, 42)
    const camera = new THREE.PerspectiveCamera(42, 1, 0.02, 200)
    camera.up.set(0, 1, 0)
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.shadowMap.enabled = true
    mount.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.08
    controls.minDistance = 2
    controls.maxDistance = 45
    controls.target.set(project.geometry.lwl_m * 0.48, project.geometry.depth_m * 0.42, 0)

    scene.add(new THREE.HemisphereLight('#d8fbff', '#082331', 1.8))
    const key = new THREE.DirectionalLight('#ffffff', 3.1)
    key.position.set(-4, 9, 7)
    key.castShadow = true
    scene.add(key)
    const rim = new THREE.DirectionalLight('#28d9e8', 2.2)
    rim.position.set(10, 3, -8)
    scene.add(rim)

    const grid = new THREE.GridHelper(24, 32, '#315b69', '#173844')
    grid.position.set(project.geometry.lwl_m * 0.46, 0, 0)
    scene.add(grid)
    const axes = new THREE.AxesHelper(1.1)
    axes.position.set(-0.05, 0.02, 0)
    scene.add(axes)

    const meshData = evaluation.results.geometry_3d
    const positions = new Float32Array(meshData.vertices.flat())
    const indices = new Uint32Array(meshData.faces.flat())
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setIndex(new THREE.BufferAttribute(indices, 1))
    geometry.computeVertexNormals()
    geometry.computeBoundingSphere()
    const hullMaterial = new THREE.MeshPhysicalMaterial({
      color: '#06a9c2',
      metalness: 0.08,
      roughness: 0.28,
      clearcoat: 0.55,
      clearcoatRoughness: 0.28,
      transparent: true,
      opacity: 0.88,
      side: THREE.DoubleSide,
    })
    const hull = new THREE.Mesh(geometry, hullMaterial)
    hull.castShadow = true
    hull.receiveShadow = true
    // Core coordinates already use Y-up. No corrective rotation is applied.
    scene.add(hull)

    const draft = numberValue(evaluation.results.hydrostatics.draft_m, project.geometry.design_draft_m)
    const waterGeometry = new THREE.PlaneGeometry(project.geometry.lwl_m * 1.18, project.geometry.beam_m * 2.2)
    const waterMaterial = new THREE.MeshPhysicalMaterial({
      color: '#126884',
      transparent: true,
      opacity: 0.27,
      side: THREE.DoubleSide,
      roughness: 0.18,
    })
    const water = new THREE.Mesh(waterGeometry, waterMaterial)
    water.rotation.x = -Math.PI / 2
    water.position.set(project.geometry.lwl_m * 0.48, draft, 0)
    scene.add(water)

    const markerObjects: THREE.Object3D[] = []
    const addMarker = (label: string, color: string, x: number, y: number, z: number, radius = 0.09) => {
      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 18, 18),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.55 }),
      )
      marker.position.set(x, y, z)
      scene.add(marker)
      markerObjects.push(marker)
      const labelSprite = textSprite(label, color)
      labelSprite.position.set(x, y + 0.24, z)
      scene.add(labelSprite)
      markerObjects.push(labelSprite)
    }
    const weightData = evaluation.results.weights
    const hydro = evaluation.results.hydrostatics
    addMarker('CG', '#ffd166', weightData.lcg_m, weightData.vcg_m, weightData.tcg_m, 0.11)
    addMarker('CB', '#6ee7b7', numberValue(hydro.lcb_m), numberValue(hydro.kb_m), 0, 0.10)
    project.downflooding_points.forEach((point, index) => {
      addMarker(
        `DF${index + 1}`,
        '#ff6b9a',
        numberValue(point.x_m),
        numberValue(point.z_m, project.geometry.depth_m),
        numberValue(point.y_m),
        0.075,
      )
    })

    project.tanks.forEach((tank) => {
      const length = numberValue(tank.length_m, 0.8)
      const width = numberValue(tank.width_m, 0.5)
      const height = numberValue(tank.height_m, 0.3)
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(length, height, width),
        new THREE.MeshStandardMaterial({ color: '#d8c94b', transparent: true, opacity: 0.35, wireframe: true }),
      )
      box.position.set(
        numberValue(tank.lcg_m),
        Math.max(height / 2, numberValue(tank.vcg_m, height / 2)),
        numberValue(tank.tcg_m),
      )
      scene.add(box)
      markerObjects.push(box)
    })

    const engineCount = numberValue(evaluation.results.propulsion.selected_engine?.quantity, 1)
    for (let index = 0; index < Math.min(4, engineCount); index += 1) {
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(0.36, 0.58, 0.30),
        new THREE.MeshStandardMaterial({ color: '#9c5cff', roughness: 0.5 }),
      )
      box.position.set(0.12, 0.68, (index - (engineCount - 1) / 2) * 0.42)
      scene.add(box)
      markerObjects.push(box)
    }

    const L = project.geometry.lwl_m
    const D = project.geometry.depth_m
    const B = project.geometry.beam_m
    const setView = (view: ViewName) => {
      const target = new THREE.Vector3(L * 0.48, D * 0.43, 0)
      if (view === 'side') camera.position.set(L * 0.48, D * 0.70, B * 3.0)
      if (view === 'bow') camera.position.set(L * 1.42, D * 0.62, 0.02)
      if (view === 'top') camera.position.set(L * 0.48, L * 1.35, 0.01)
      if (view === 'iso') camera.position.set(L * 1.10, D * 3.2, B * 2.25)
      if (view === 'top') camera.up.set(0, 0, -1)
      else camera.up.set(0, 1, 0)
      controls.target.copy(target)
      camera.lookAt(target)
      controls.update()
    }
    viewHandlerRef.current = setView
    setView(activeView)

    const resize = () => {
      const width = Math.max(280, mount.clientWidth)
      const height = Math.max(360, mount.clientHeight)
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    }
    const observer = new ResizeObserver(resize)
    observer.observe(mount)
    resize()

    let frame = 0
    const animate = () => {
      frame = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      geometry.dispose()
      hullMaterial.dispose()
      waterGeometry.dispose()
      waterMaterial.dispose()
      markerObjects.forEach((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose()
          if (Array.isArray(object.material)) object.material.forEach((item) => item.dispose())
          else object.material.dispose()
        }
        if (object instanceof THREE.Sprite) {
          const texture = object.userData.texture as THREE.Texture | undefined
          texture?.dispose()
          object.material.dispose()
        }
      })
      renderer.dispose()
      renderer.domElement.remove()
      viewHandlerRef.current = () => undefined
    }
  }, [project, evaluation, activeView])

  const changeView = (view: ViewName) => {
    setActiveView(view)
    viewHandlerRef.current(view)
  }

  return (
    <div className="hull-viewer">
      <div className="viewer-controls" aria-label="Vistas do casco">
        {(['iso', 'side', 'bow', 'top'] as ViewName[]).map((view) => (
          <button
            type="button"
            key={view}
            className={activeView === view ? 'active' : ''}
            onClick={() => changeView(view)}
          >
            {{ iso: 'ISO', side: 'LADO', bow: 'PROA', top: 'TOPO' }[view]}
          </button>
        ))}
      </div>
      <div ref={mountRef} className="hull-canvas" />
      <div className="viewer-legend">
        <span className="cg">CG</span>
        <span className="cb">Centro de carena</span>
        <span className="df">Downflooding</span>
      </div>
    </div>
  )
}
