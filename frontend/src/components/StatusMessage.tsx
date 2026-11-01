interface Props {
  message: string;
  onRetry?: () => void;
}

/** A problem the buyer can act on: what went wrong, and a way to try again. */
export function StatusMessage({ message, onRetry }: Props) {
  return (
    <div className="status" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="button" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}
