import React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

const Dialog = ({ open, onOpenChange, children }) => {
  if (!open) return null;
  return children;
};

const DialogTrigger = ({ children, onClick }) => {
  return React.cloneElement(children, { onClick });
};

const DialogOverlay = ({ className, onClick, ...props }) => (
  <div
    className={cn(
      'fixed inset-0 z-50 bg-black/80 transition-opacity',
      className
    )}
    onClick={onClick}
    {...props}
  />
);

const DialogContent = ({ className, children, onClose, ...props }) => (
  <>
    <DialogOverlay onClick={onClose} />
    <div
      className={cn(
        'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg transition-all sm:rounded-lg',
        className
      )}
      {...props}
    >
      {children}
      <button
        className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
        onClick={onClose}
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </button>
    </div>
  </>
);

const DialogHeader = ({ className, ...props }) => (
  <div
    className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)}
    {...props}
  />
);

const DialogFooter = ({ className, ...props }) => (
  <div
    className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2', className)}
    {...props}
  />
);

const DialogTitle = ({ className, ...props }) => (
  <h2
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
);

const DialogDescription = ({ className, ...props }) => (
  <p
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
);

const DialogClose = ({ children, onClick }) => {
  return React.cloneElement(children, { onClick });
};

const DialogPortal = ({ children }) => {
  return children;
};

export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};
