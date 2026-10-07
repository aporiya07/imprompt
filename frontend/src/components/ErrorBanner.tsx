import { CircleAlert, X } from "lucide-react";

interface Props {
  message: string;
  onDismiss: () => void;
  actionLabel?: string;
  onAction?: () => void;
  code?: string;
  requestId?: string;
}

export default function ErrorBanner({ message, onDismiss, actionLabel, onAction, code, requestId }: Props) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-icon">
        <CircleAlert size={16} />
      </span>
      <div className="error-body">
        <div className="error-label">Request failed</div>
        <span className="error-msg">{message}</span>
        {(code || requestId) && (
          <details className="error-details">
            <summary>Technical details</summary>
            <pre>{`code: ${code ?? "unknown"}\nrequest_id: ${requestId ?? "unknown"}`}</pre>
          </details>
        )}
      </div>
      {actionLabel && onAction && (
        <button className="btn small banner-action" onClick={onAction}>
          {actionLabel}
        </button>
      )}
      <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss error">
        <X size={15} />
      </button>
    </div>
  );
}
