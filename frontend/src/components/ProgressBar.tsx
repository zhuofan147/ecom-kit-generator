type ProgressBarProps = {
  value: number;
  label: string;
};

export function ProgressBar({ value, label }: ProgressBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded bg-slate-200">
        <div className="h-full rounded bg-action transition-all" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
