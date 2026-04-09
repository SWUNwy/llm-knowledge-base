import { ReactNode } from "react";

type IconColor = "blue" | "purple" | "green";

interface IconBoxProps {
  color: IconColor;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const colorStyles: Record<IconColor, string> = {
  blue: "from-brand-blue to-brand-blue-light",
  purple: "from-brand-purple to-brand-purple-light",
  green: "from-brand-green to-brand-green-light",
};

const sizeStyles = {
  sm: "w-8 h-8 text-base",
  md: "w-12 h-12 text-2xl",
  lg: "w-14 h-14 text-[28px]",
};

export function IconBox({ color, children, size = "md", className = "" }: IconBoxProps) {
  return (
    <div
      className={`bg-gradient-to-br ${colorStyles[color]} ${sizeStyles[size]} rounded-[12px] flex items-center justify-center ${className}`}
    >
      {children}
    </div>
  );
}
