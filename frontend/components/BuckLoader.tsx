"use client";

/** A whitetail buck walking in place, used while the freezer loads.
 *  Pure SVG + CSS: legs swing from the hip in a walking gait, the body bobs,
 *  and the ground scrolls under him. Still image when reduced motion is on. */
export default function BuckLoader({
  size = 120,
  label,
  className = "",
}: {
  size?: number;
  label?: string;
  className?: string;
}) {
  return (
    <div className={`buck-loader ${className}`} role="status" aria-live="polite">
      <svg
        className="buck"
        width={size}
        height={size * 0.733}
        viewBox="0 -10 120 88"
        aria-hidden="true"
      >
        {/* far legs (dimmer, opposite phase) */}
        <g className="leg leg-far leg-a">
          <path d="M71 47 L72 60 L70 72 L70.5 76" />
        </g>
        <g className="leg leg-far leg-b">
          <path d="M39 46 L37 58 L40 70 L39.5 76" />
        </g>

        <g className="buck-body">
          {/* tail */}
          <path className="fill" d="M33 37 Q27 33 28 40 Q30 42 34 41 Z" />
          <path className="tail-white" d="M29.5 38.5 Q29 40.5 31 40.8" />
          {/* body */}
          <path
            className="fill"
            d="M34 38 Q36 30 50 30 L68 30 Q76 29 79 33 Q82 40 79 48 Q76 52 68 52 L44 52 Q35 51 34 44 Z"
          />
          {/* neck */}
          <path className="fill" d="M70 34 Q76 24 84 16 L91 19 Q86 30 80 40 Z" />
          {/* head */}
          <path className="fill" d="M82 15 Q87 10 93 13 L101 18 Q103 20.5 100 21.5 L92 22 Q85 21 82 18 Z" />
          {/* ear */}
          <path className="fill" d="M85 13 Q81 7 79 8 Q80 12 84 15 Z" />
          {/* eye */}
          <circle className="eye" cx="91" cy="15.5" r="0.9" />
          {/* antlers */}
          <path
            className="antler"
            d="M87 11 Q82 5 83 0 Q85 -4 94 -3 M84.5 -1.5 L82 -7 M88 -3.2 L87.5 -8.5 M91.5 -3.4 L92.5 -7.5 M87.5 9.5 Q91 6 90 3"
          />
        </g>

        {/* near legs */}
        <g className="leg leg-near leg-b">
          <path d="M74 47 L75 60 L73 72 L73.5 76" />
        </g>
        <g className="leg leg-near leg-a">
          <path d="M42 46 L40 58 L43 70 L42.5 76" />
        </g>

        {/* ground */}
        <line className="ground" x1="0" y1="77" x2="120" y2="77" />
      </svg>
      {label ? <div className="buck-label">{label}</div> : null}
    </div>
  );
}
