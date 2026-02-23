from rest_framework import serializers

class AnalyticsSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_users = serializers.IntegerField()
    active_courses = serializers.IntegerField()
    platform_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

class TrendPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    new_users = serializers.IntegerField()

class TopCourseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    enrollments = serializers.IntegerField()

class CategoryDistributionSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.IntegerField()

class DashboardAnalyticsSerializer(serializers.Serializer):
    summary = AnalyticsSummarySerializer()
    trend = TrendPointSerializer(many=True)
    top_courses = TopCourseSerializer(many=True)
    category_distribution = CategoryDistributionSerializer(many=True)
