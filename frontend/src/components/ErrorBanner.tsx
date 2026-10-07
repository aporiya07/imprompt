interface Props {
  message: string;
  onDismiss: () => void;
  actionLabel?: string;
  onAction?: () => void;
}

export default function ErrorBanner({ message, onDismiss, actionLabel, onAction }: Props) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-icon">⚠</span>
      <span className="error-msg">{message}</span>
      {actionLabel && onAction && (
        <button className="btn small banner-action" onClick={onAction}>
          {actionLabel}
        </button>
      )}
      <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
