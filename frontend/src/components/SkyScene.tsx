import { useEffect, useRef } from 'react'

import { initSkyAnimation } from '../lib/skyScene'

export function SkyScene() {
  const starsRef = useRef<SVGGElement>(null)
  const sceneRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!starsRef.current || !sceneRef.current) {
      return undefined
    }

    return initSkyAnimation(starsRef.current, sceneRef.current)
  }, [])

  return (
    <div ref={sceneRef} className="sky-scene" aria-hidden="true">
      <svg
        className="sky-milky-way"
        viewBox="0 0 1000 600"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter id="milkyWayBlur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="28" />
          </filter>
          <radialGradient id="milkyWayCore" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(220, 230, 255, 0.16)" />
            <stop offset="40%" stopColor="rgba(200, 215, 245, 0.1)" />
            <stop offset="100%" stopColor="rgba(180, 195, 230, 0)" />
          </radialGradient>
          <radialGradient id="milkyWayHaze" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(200, 215, 245, 0.08)" />
            <stop offset="100%" stopColor="rgba(180, 195, 230, 0)" />
          </radialGradient>
        </defs>
        <ellipse
          cx="500"
          cy="300"
          rx="920"
          ry="85"
          transform="rotate(32 500 300)"
          fill="url(#milkyWayHaze)"
          filter="url(#milkyWayBlur)"
          opacity="0.4"
        />
        <ellipse
          cx="500"
          cy="300"
          rx="920"
          ry="85"
          transform="rotate(32 500 300)"
          fill="url(#milkyWayCore)"
          filter="url(#milkyWayBlur)"
        />
      </svg>

      <svg className="sky-stars" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid slice">
        <g ref={starsRef} fill="#e8edf5" />
      </svg>

      <svg className="sky-moon" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid slice">
        <defs>
          <filter id="moonGlow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="14" />
          </filter>
          <radialGradient id="moonHalo" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(235, 240, 252, 0.28)" />
            <stop offset="45%" stopColor="rgba(200, 210, 235, 0.1)" />
            <stop offset="100%" stopColor="rgba(140, 155, 190, 0)" />
          </radialGradient>
          <radialGradient id="moonDisk" cx="42%" cy="38%" r="58%">
            <stop offset="0%" stopColor="#f6f8fc" />
            <stop offset="72%" stopColor="#e4eaf4" />
            <stop offset="100%" stopColor="#c8d2e4" />
          </radialGradient>
        </defs>
        <g className="sky-moon-art">
          <circle cx="872" cy="88" r="105" fill="url(#moonHalo)" />
          <circle
            cx="872"
            cy="88"
            r="72"
            fill="rgba(225, 232, 248, 0.1)"
            filter="url(#moonGlow)"
          />
          <circle cx="872" cy="88" r="31" fill="url(#moonDisk)" />
          <circle cx="864" cy="80" r="5.5" fill="rgba(205, 215, 230, 0.22)" />
          <circle cx="882" cy="93" r="3.8" fill="rgba(205, 215, 230, 0.16)" />
          <circle cx="876" cy="98" r="2.6" fill="rgba(205, 215, 230, 0.12)" />
        </g>
      </svg>
    </div>
  )
}
