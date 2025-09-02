import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Receipt, 
  TrendingUp, 
  DollarSign, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  FileText,
  Calendar,
  ArrowUpRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { receiptAPI, analyticsAPI } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalReceipts: 0,
    totalAmount: 0,
    pendingReviews: 0,
    categoryBreakdown: [],
    monthlyTrends: []
  });
  const [recentReceipts, setRecentReceipts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load analytics and recent receipts in parallel
      const [analyticsResponse, receiptsResponse] = await Promise.all([
        analyticsAPI.getSummary(),
        receiptAPI.getAll({ limit: 5, offset: 0 })
      ]);

      const analyticsData = analyticsResponse.data;
      const receiptsData = receiptsResponse.data;

      setStats({
        totalReceipts: analyticsData.total_receipts || 0,
        totalAmount: analyticsData.category_breakdown?.reduce((sum, cat) => sum + (cat.total_amount || 0), 0) || 0,
        pendingReviews: receiptsData.filter(r => r.manual_review_needed).length,
        categoryBreakdown: analyticsData.category_breakdown || [],
        monthlyTrends: analyticsData.monthly_trends || []
      });

      setRecentReceipts(receiptsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's your receipt overview.</p>
        </div>
        <Link to="/upload">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Upload className="h-4 w-4 mr-2" />
            Upload Receipt
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Receipts</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalReceipts}</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-full">
                <Receipt className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-500 font-medium">+12%</span>
              <span className="text-gray-600 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Amount</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.totalAmount)}</p>
              </div>
              <div className="bg-green-50 p-3 rounded-full">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-500 font-medium">+8%</span>
              <span className="text-gray-600 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pendingReviews}</p>
              </div>
              <div className="bg-orange-50 p-3 rounded-full">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <AlertCircle className="h-4 w-4 text-orange-500 mr-1" />
              <span className="text-orange-500 font-medium">Needs attention</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">AI Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">96%</p>
              </div>
              <div className="bg-purple-50 p-3 rounded-full">
                <CheckCircle className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-500 font-medium">+2%</span>
              <span className="text-gray-600 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Receipts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-semibold">Recent Receipts</CardTitle>
            <Link to="/receipts">
              <Button variant="outline" size="sm">
                View All
                <ArrowUpRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentReceipts.map((receipt) => (
                <div key={receipt.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-50 p-2 rounded-lg">
                      <FileText className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {receipt.extracted_data?.vendor_name || receipt.filename}
                      </p>
                      <p className="text-sm text-gray-500 flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        {formatDate(receipt.upload_timestamp)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {formatCurrency(receipt.extracted_data?.total_amount)}
                    </p>
                    {receipt.category && (
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(receipt.category)}`}>
                        {receipt.category.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              
              {recentReceipts.length === 0 && (
                <div className="text-center py-8">
                  <Receipt className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No receipts found</p>
                  <p className="text-sm text-gray-400">Upload your first receipt to get started</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Expense Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.categoryBreakdown.slice(0, 6).map((category) => (
                <div key={category._id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getCategoryColor(category._id).split(' ')[0]}`}></div>
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {category._id?.replace('_', ' ') || 'Other'}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">
                      {formatCurrency(category.total_amount)}
                    </p>
                    <p className="text-xs text-gray-500">{category.count} receipts</p>
                  </div>
                </div>
              ))}
              
              {stats.categoryBreakdown.length === 0 && (
                <div className="text-center py-8">
                  <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No category data yet</p>
                  <p className="text-sm text-gray-400">Upload receipts to see expense breakdown</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/upload">
              <Button variant="outline" className="h-20 w-full flex flex-col items-center justify-center space-y-2">
                <Upload className="h-6 w-6" />
                <span>Upload Receipt</span>
              </Button>
            </Link>
            
            <Link to="/receipts?status=pending">
              <Button variant="outline" className="h-20 w-full flex flex-col items-center justify-center space-y-2">
                <Clock className="h-6 w-6" />
                <span>Review Pending</span>
              </Button>
            </Link>
            
            <Link to="/analytics">
              <Button variant="outline" className="h-20 w-full flex flex-col items-center justify-center space-y-2">
                <TrendingUp className="h-6 w-6" />
                <span>View Analytics</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;