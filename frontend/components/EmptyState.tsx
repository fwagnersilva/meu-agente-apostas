export default function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <p className="text-sm">{message}</p>
    </div>
  );
}
