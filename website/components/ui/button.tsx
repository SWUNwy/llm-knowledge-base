import { ReactNode } from "react";

type ButtonVariant = "primary" | "outline" | "outline-white";

interface ButtonProps {
  variant: ButtonVariant;
  children: ReactNode;
  href?: string;
  className?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-brand-blue to-brand-purple text-white font-semibold",
  outline:
    "border border-slate-300 text-text-primary font-medium hover:border-slate-400 transition-colors",
  "outline-white":
    "border border-slate-600 text-text-on-dark font-medium hover:border-slate-400 transition-colors",
};

export function Button({ variant, children, href, className = "" }: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center px-7 py-3.5 rounded-button text-[15px] cursor-pointer";
  const styles = `${baseStyles} ${variantStyles[variant]} ${className}`;

  if (href) {
    return (
      <a href={href} className={styles}>
        {children}
      </a>
    );
  }

  return <button className={styles}>{children}</button>;
}
