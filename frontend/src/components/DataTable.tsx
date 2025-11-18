'use client';

interface DataTableProps {
  data: any[];
  columns?: string[];
}

export default function DataTable({ data, columns }: DataTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data to display
      </div>
    );
  }

  const cols = columns || Object.keys(data[0]);

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {cols.map((col) => (
              <th
                key={col}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {cols.map((col) => (
                <td
                  key={col}
                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                >
                  {row[col] !== null && row[col] !== undefined
                    ? String(row[col])
                    : '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
