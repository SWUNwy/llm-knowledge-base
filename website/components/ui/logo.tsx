import { SITE_NAME } from "@/lib/constants";

interface LogoProps {
  className?: string;
}

export function Logo({ className = "" }: LogoProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="w-7 h-7 rounded-md bg-gradient-to-br from-brand-blue to-brand-purple" />
      <span className="text-white font-bold text-base">{SITE_NAME}</span>
    </div>
  );
}
