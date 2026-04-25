export default function LoadingSpinner({ text = "Carregando..." }: { text?: string }) {
  return (
    <div className="flex items-center gap-3 text-gray-500 py-12 justify-center">
      <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm">{text}</span>
    </div>
  );
}
