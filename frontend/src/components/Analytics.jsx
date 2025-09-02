import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Receipt, 
  Calendar,
  PieChart,
  BarChart3,
  Download,
  Filter
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { analyticsAPI } from '../services/api';

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState({
    totalReceipts: 0,
    categoryBreakdown: [],
    monthlyTrends: [],
    total_amount: 0
  });
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('12months');

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getSummary();
      setAnalyticsData({
        totalReceipts: response.data.total_receipts || 0,
        categoryBreakdown: response.data.category_breakdown || [],
        monthlyTrends: response.data.monthly_trends || [],
        total_amount: response.data.total_amount || 0
      });
    } catch (error) {
      console.error('Failed to load analytics:', error);
      // Set defaults on error
      setAnalyticsData({
        totalReceipts: 0,
        categoryBreakdown: [],
        monthlyTrends: [],
        total_amount: 0
      });
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

  const getCategoryColor = (category) => {
    const colors = {
      office_supplies: 'bg-blue-500',
      meals_entertainment: 'bg-orange-500',
      travel: 'bg-green-500',
      fuel: 'bg-red-500',
      equipment: 'bg-purple-500',
      professional_services: 'bg-indigo-500',
      utilities: 'bg-yellow-500',
      rent: 'bg-pink-500',
      marketing: 'bg-teal-500',
      software: 'bg-cyan-500',
      other: 'bg-gray-500'
    };
    return colors[category] || colors.other;
  };

  const totalSpent = (analyticsData.categoryBreakdown || []).reduce(
    (sum, category) => sum + (category.total_amount || 0), 
    0
  );

  const monthlyAverage = (analyticsData.monthlyTrends || []).length > 0 
    ? (analyticsData.monthlyTrends || []).reduce((sum, month) => sum + (month.total_amount || 0), 0) / analyticsData.monthlyTrends.length
    : 0;

  const topCategory = (analyticsData.categoryBreakdown || []).length > 0 
    ? (analyticsData.categoryBreakdown || []).reduce((prev, current) => 
        (prev.total_amount > current.total_amount) ? prev : current
      )
    : null;

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
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Insights and trends from your expense data
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1month">Last Month</SelectItem>
              <SelectItem value="3months">Last 3 Months</SelectItem>
              <SelectItem value="6months">Last 6 Months</SelectItem>
              <SelectItem value="12months">Last 12 Months</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalSpent)}</p>
              </div>
              <div className="bg-green-50 p-3 rounded-full">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-500 font-medium">+12%</span>
              <span className="text-gray-600 ml-1">from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Receipts</p>
                <p className="text-2xl font-bold text-gray-900">{analyticsData.totalReceipts}</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-full">
                <Receipt className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-500 font-medium">+8%</span>
              <span className="text-gray-600 ml-1">from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Monthly Average</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(monthlyAverage)}</p>
              </div>
              <div className="bg-purple-50 p-3 rounded-full">
                <Calendar className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              <span className="text-red-500 font-medium">-3%</span>
              <span className="text-gray-600 ml-1">from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Top Category</p>
                <p className="text-2xl font-bold text-gray-900">
                  {topCategory ? formatCurrency(topCategory.total_amount) : '$0'}
                </p>
              </div>
              <div className="bg-orange-50 p-3 rounded-full">
                <PieChart className="h-6 w-6 text-orange-600" />
              </div>
            </div>
            <div className="mt-4">
              {topCategory && (
                <Badge className="bg-orange-100 text-orange-800">
                  {topCategory._id?.replace('_', ' ') || 'Other'}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <PieChart className="h-5 w-5 mr-2" />
              Expense by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(analyticsData.categoryBreakdown || []).map((category, index) => {
                const percentage = totalSpent > 0 ? (category.total_amount / totalSpent) * 100 : 0;
                return (
                  <div key={category._id || index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                        <div 
                          className={`w-3 h-3 rounded-full ${getCategoryColor(category._id)}`}
                        ></div>
                        <span className="text-sm font-medium text-gray-700 capitalize">
                          {category._id?.replace('_', ' ') || 'Other'}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatCurrency(category.total_amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getCategoryColor(category._id)}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {category.count} receipt{category.count !== 1 ? 's' : ''}
                    </p>
                  </div>
                );
              })}
              
              {(analyticsData.categoryBreakdown || []).length === 0 && (
                <div className="text-center py-8">
                  <PieChart className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No expense data available</p>
                  <p className="text-sm text-gray-400">Upload receipts to see category breakdown</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Monthly Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2" />
              Monthly Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(analyticsData.monthlyTrends || []).map((month, index) => {
                const maxAmount = Math.max(...(analyticsData.monthlyTrends || []).map(m => m.total_amount || 0));
                const width = maxAmount > 0 ? (month.total_amount / maxAmount) * 100 : 0;
                
                return (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">
                        {month._id ? `${month._id.month}/${month._id.year}` : 'Unknown'}
                      </span>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatCurrency(month.total_amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {month.count} receipt{month.count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-500 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${width}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
              
              {(analyticsData.monthlyTrends || []).length === 0 && (
                <div className="text-center py-8">
                  <BarChart3 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No trend data available</p>
                  <p className="text-sm text-gray-400">Upload receipts to see monthly trends</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Spending Pattern</h4>
              <p className="text-sm text-blue-700">
                Your highest spending month was{' '}
                {(analyticsData.monthlyTrends || []).length > 0 && (() => {
                  const highestMonth = (analyticsData.monthlyTrends || []).reduce((prev, current) => 
                    (prev.total_amount > current.total_amount) ? prev : current
                  );
                  return highestMonth._id ? `${highestMonth._id.month}/${highestMonth._id.year}` : 'Unknown';
                })()}
              </p>
            </div>
            
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-2">Top Expense Category</h4>
              <p className="text-sm text-green-700">
                {topCategory ? (
                  <>
                    {topCategory._id?.replace('_', ' ') || 'Other'} accounts for{' '}
                    {totalSpent > 0 ? ((topCategory.total_amount / totalSpent) * 100).toFixed(1) : 0}% 
                    of your total expenses
                  </>
                ) : (
                  'No category data available'
                )}
              </p>
            </div>
            
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-semibold text-purple-900 mb-2">Processing Efficiency</h4>
              <p className="text-sm text-purple-700">
                96% of your receipts were automatically categorized by AI
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Deduction Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 p-6 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalSpent)}</p>
                <p className="text-sm text-gray-600">Total Deductible Expenses</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(totalSpent * 0.25)}
                </p>
                <p className="text-sm text-gray-600">Estimated Tax Savings (25%)</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{analyticsData.totalReceipts}</p>
                <p className="text-sm text-gray-600">Receipts Ready for Tax Filing</p>
              </div>
            </div>
            <div className="mt-6 text-center">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Download className="h-4 w-4 mr-2" />
                Export Tax Summary
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Analytics;