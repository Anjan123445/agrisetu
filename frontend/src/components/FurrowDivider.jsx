// The site's signature element: parallel wavy lines evoking ploughed field
// rows (furrows). Used as a section divider instead of a generic rule.
export default function FurrowDivider({ className = "", tone = "leaf" }) {
  const strokeColor =
    tone === "leaf" ? "var(--color-leaf)" : tone === "marigold" ? "var(--color-marigold)" : "var(--color-earth)";

  return (
    <div className={`w-full overflow-hidden ${className}`} aria-hidden="true">
      <svg viewBox="0 0 400 28" preserveAspectRatio="none" className="w-full h-5 sm:h-7">
        {[4, 12, 20].map((y, i) => (
          <path
            key={y}
            d={`M0 ${y} Q 25 ${y - 6}, 50 ${y} T 100 ${y} T 150 ${y} T 200 ${y} T 250 ${y} T 300 ${y} T 350 ${y} T 400 ${y}`}
            fill="none"
            stroke={strokeColor}
            strokeWidth="2"
            strokeLinecap="round"
            opacity={1 - i * 0.28}
          />
        ))}
      </svg>
    </div>
  );
}
