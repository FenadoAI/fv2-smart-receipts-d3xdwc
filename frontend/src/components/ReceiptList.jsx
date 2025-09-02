import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Eye, 
  Edit3, 
  Trash2, 
  Download, 
  Calendar,
  DollarSign,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  MoreHorizontal
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { receiptAPI } from '../services/api';

const ReceiptList = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadReceipts();
  }, [categoryFilter, statusFilter]);

  const loadReceipts = async () => {
    try {
      setLoading(true);
      const params = {};
      
      if (categoryFilter !== 'all') {
        params.category = categoryFilter;
      }
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const response = await receiptAPI.getAll(params);
      setReceipts(response.data);
    } catch (error) {
      console.error('Failed to load receipts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (receiptId) => {
    if (window.confirm('Are you sure you want to delete this receipt?')) {
      try {
        await receiptAPI.delete(receiptId);
        setReceipts(prev => prev.filter(r => r.id !== receiptId));
      } catch (error) {
        console.error('Failed to delete receipt:', error);
      }
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getCategoryColor = (category) => {
    const colors = {
      office_supplies: 'bg-blue-100 text-blue-800',
      meals_entertainment: 'bg-orange-100 text-orange-800',
      travel: 'bg-green-100 text-green-800',
      fuel: 'bg-red-100 text-red-800',
      equipment: 'bg-purple-100 text-purple-800',
      professional_services: 'bg-indigo-100 text-indigo-800',
      utilities: 'bg-yellow-100 text-yellow-800',
      rent: 'bg-pink-100 text-pink-800',
      marketing: 'bg-teal-100 text-teal-800',
      software: 'bg-cyan-100 text-cyan-800',
      other: 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.other;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const filteredReceipts = receipts.filter(receipt => {
    const matchesSearch = !searchTerm || 
      receipt.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      receipt.extracted_data?.vendor_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'office_supplies', label: 'Office Supplies' },
    { value: 'meals_entertainment', label: 'Meals & Entertainment' },
    { value: 'travel', label: 'Travel' },
    { value: 'fuel', label: 'Fuel' },
    { value: 'equipment', label: 'Equipment' },
    { value: 'professional_services', label: 'Professional Services' },
    { value: 'utilities', label: 'Utilities' },
    { value: 'rent', label: 'Rent' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'software', label: 'Software' },
    { value: 'other', label: 'Other' }
  ];

  const statuses = [
    { value: 'all', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' }
  ];

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Receipts</h1>
          <p className="text-gray-600 mt-1">
            Manage and review all your uploaded receipts
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {filteredReceipts.length} of {receipts.length} receipts
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search receipts by filename or vendor..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map(category => (
                  <SelectItem key={category.value} value={category.value}>
                    {category.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                {statuses.map(status => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Receipts List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredReceipts.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts found</h3>
              <p className="text-gray-500">
                {receipts.length === 0 
                  ? "Upload your first receipt to get started"
                  : "Try adjusting your search or filters"
                }
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredReceipts.map((receipt) => (
                <div key={receipt.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    {/* Receipt Info */}
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <FileText className="h-6 w-6 text-blue-600" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-semibold text-gray-900 truncate">
                            {receipt.extracted_data?.vendor_name || receipt.filename}
                          </h3>
                          {getStatusIcon(receipt.processing_status)}
                        </div>
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {formatDate(receipt.upload_timestamp)}
                          </span>
                          {receipt.extracted_data?.date && (
                            <span className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1" />
                              Receipt: {formatDate(receipt.extracted_data.date)}
                            </span>
                          )}
                          <span className="text-xs text-gray-400">
                            {(receipt.file_size / 1024).toFixed(1)} KB
                          </span>
                        </div>

                        {receipt.extracted_data?.description && (
                          <p className="text-sm text-gray-600 mt-1 truncate">
                            {receipt.extracted_data.description}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Amount & Category */}
                    <div className="text-right mr-4">
                      {receipt.extracted_data?.total_amount && (
                        <p className="text-lg font-bold text-gray-900 flex items-center">
                          <DollarSign className="h-4 w-4 mr-1" />
                          {formatCurrency(receipt.extracted_data.total_amount)}
                        </p>
                      )}
                      {receipt.category && (
                        <Badge className={`mt-1 ${getCategoryColor(receipt.category)}`}>
                          {receipt.category.replace('_', ' ')}
                        </Badge>
                      )}
                      {receipt.manual_review_needed && (
                        <Badge variant="destructive" className="mt-1 ml-2">
                          Needs Review
                        </Badge>
                      )}
                    </div>

                    {/* Actions */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem 
                          onClick={() => {
                            setSelectedReceipt(receipt);
                            setShowDetails(true);
                          }}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Edit3 className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDelete(receipt.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Receipt Details Modal */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Receipt Details</DialogTitle>
          </DialogHeader>
          
          {selectedReceipt && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Filename</label>
                  <p className="text-sm text-gray-900">{selectedReceipt.filename}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Upload Date</label>
                  <p className="text-sm text-gray-900">{formatDate(selectedReceipt.upload_timestamp)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Processing Status</label>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(selectedReceipt.processing_status)}
                    <span className="text-sm capitalize">{selectedReceipt.processing_status}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Confidence Score</label>
                  <p className="text-sm text-gray-900">
                    {selectedReceipt.confidence_score ? 
                      `${(selectedReceipt.confidence_score * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </p>
                </div>
              </div>

              {/* Extracted Data */}
              {selectedReceipt.extracted_data && (
                <div className="border-t pt-6">
                  <h4 className="font-medium text-gray-900 mb-4">Extracted Information</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Vendor</label>
                      <p className="text-sm text-gray-900">
                        {selectedReceipt.extracted_data.vendor_name || 'Not detected'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Total Amount</label>
                      <p className="text-sm text-gray-900">
                        {selectedReceipt.extracted_data.total_amount ? 
                          formatCurrency(selectedReceipt.extracted_data.total_amount) : 
                          'Not detected'
                        }
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Tax Amount</label>
                      <p className="text-sm text-gray-900">
                        {selectedReceipt.extracted_data.tax_amount ? 
                          formatCurrency(selectedReceipt.extracted_data.tax_amount) : 
                          'Not detected'
                        }
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Receipt Date</label>
                      <p className="text-sm text-gray-900">
                        {selectedReceipt.extracted_data.date ? 
                          formatDate(selectedReceipt.extracted_data.date) : 
                          'Not detected'
                        }
                      </p>
                    </div>
                    <div className="col-span-2">
                      <label className="text-sm font-medium text-gray-500">Description</label>
                      <p className="text-sm text-gray-900">
                        {selectedReceipt.extracted_data.description || 'Not detected'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Category & Tags */}
              <div className="border-t pt-6">
                <h4 className="font-medium text-gray-900 mb-4">Classification</h4>
                <div className="space-y-2">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Category</label>
                    <div className="mt-1">
                      {selectedReceipt.category ? (
                        <Badge className={getCategoryColor(selectedReceipt.category)}>
                          {selectedReceipt.category.replace('_', ' ')}
                        </Badge>
                      ) : (
                        <span className="text-sm text-gray-500">Not categorized</span>
                      )}
                    </div>
                  </div>
                  {selectedReceipt.tags && selectedReceipt.tags.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Tags</label>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {selectedReceipt.tags.map((tag, index) => (
                          <Badge key={index} variant="outline">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ReceiptList;