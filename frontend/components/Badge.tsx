type Color = "green" | "red" | "yellow" | "blue" | "gray" | "indigo" | "orange";

const colors: Record<Color, string> = {
  green: "bg-green-100 text-green-800",
  red: "bg-red-100 text-red-800",
  yellow: "bg-yellow-100 text-yellow-800",
  blue: "bg-blue-100 text-blue-800",
  gray: "bg-gray-100 text-gray-700",
  indigo: "bg-indigo-100 text-indigo-800",
  orange: "bg-orange-100 text-orange-800",
};

export default function Badge({
  label,
  color = "gray",
}: {
  label: string;
  color?: Color;
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[color]}`}
    >
      {label}
    </span>
  );
}
