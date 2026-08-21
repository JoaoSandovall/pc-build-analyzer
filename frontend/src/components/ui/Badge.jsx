export const Badge = ({ children, color = "zinc" }) => {
  const colors = {
    zinc: "bg-zinc-950 text-zinc-400 border-zinc-800",
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return (
    <span className={`inline-block px-2.5 py-1 text-[10px] font-bold rounded-md uppercase tracking-widest border shadow-sm ${colors[color] || colors.zinc}`}>
      {children}
    </span>
  );
};