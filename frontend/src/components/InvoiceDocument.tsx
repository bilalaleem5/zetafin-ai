import { forwardRef } from 'react';

export interface InvoiceUser {
  business_name: string;
  email: string;
}

export interface InvoiceClient {
  name: string;
}

export interface InvoiceMilestone {
  id: number;
  title: string;
  amount: number;
  tax_amount: number;
  tax_type: string;
  due_date: string;
}

interface Props {
  user: InvoiceUser;
  client: InvoiceClient;
  milestone: InvoiceMilestone;
}

export const InvoiceDocument = forwardRef<HTMLDivElement, Props>(({ user, client, milestone }, ref) => {
  const invoiceNumber = `INV-${new Date().getFullYear()}-${milestone.id.toString().padStart(4, '0')}`;
  const issueDate = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const dueDate = new Date(milestone.due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  
  const subtotal = milestone.amount;
  const tax = milestone.tax_amount || 0;
  const total = subtotal - tax;

  return (
    <div 
      ref={ref} 
      className="bg-white text-black p-12 mx-auto"
      style={{ width: '210mm', minHeight: '297mm', boxSizing: 'border-box', fontFamily: '"Inter", sans-serif' }}
    >
      {/* Header */}
        <div className="flex justify-between items-start mb-16">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter mb-2">{user.business_name || 'Your Company Ltd.'}</h1>
            <p className="text-gray-500 text-sm">{user.email}</p>
          </div>
          <div className="text-right">
            <h2 className="text-4xl font-light text-gray-300 uppercase tracking-widest mb-2">Invoice</h2>
            <p className="text-sm font-bold"># {invoiceNumber}</p>
          </div>
        </div>

        {/* Bill To & Details */}
        <div className="flex justify-between mb-16 pt-8 border-t border-gray-200">
          <div>
            <p className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-2">Bill To</p>
            <p className="text-xl font-medium">{client.name}</p>
          </div>
          <div className="text-right space-y-2">
            <div>
              <p className="text-gray-400 text-xs font-bold uppercase tracking-widest">Date of Issue</p>
              <p className="font-medium">{issueDate}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs font-bold uppercase tracking-widest">Due Date</p>
              <p className="font-medium">{dueDate}</p>
            </div>
          </div>
        </div>

        {/* Line Items */}
        <table className="w-full mb-16 text-left border-collapse">
          <thead>
            <tr className="border-b-2 border-black">
              <th className="py-3 text-xs font-bold uppercase tracking-widest text-gray-500 w-3/4">Description</th>
              <th className="py-3 text-xs font-bold uppercase tracking-widest text-gray-500 text-right w-1/4">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-200">
              <td className="py-6 font-medium text-lg leading-snug">{milestone.title}</td>
              <td className="py-6 text-right font-medium text-lg">PKR {subtotal.toLocaleString()}</td>
            </tr>
          </tbody>
        </table>

        {/* Totals */}
        <div className="flex justify-end">
          <div className="w-1/2 space-y-4">
            <div className="flex justify-between items-center text-gray-500">
              <span>Subtotal</span>
              <span>PKR {subtotal.toLocaleString()}</span>
            </div>
            {tax > 0 && (
              <div className="flex justify-between items-center text-gray-500">
                <span>Tax Deducted ({milestone.tax_type})</span>
                <span>- PKR {tax.toLocaleString()}</span>
              </div>
            )}
            <div className="flex justify-between items-center text-2xl font-bold pt-4 border-t-2 border-black">
              <span>Total Due</span>
              <span>PKR {total.toLocaleString()}</span>
            </div>
          </div>
        </div>

      {/* Footer */}
      <div className="mt-32 pt-8 border-t border-gray-200 text-center text-gray-400 text-sm">
        <p>Thank you for your business. Please remit payment by the due date.</p>
      </div>
    </div>
  );
});

InvoiceDocument.displayName = 'InvoiceDocument';
