from rest_framework import serializers


class AnalyticsSummarySerializer(serializers.Serializer):
    gross_revenue = serializers.FloatField()
    net_revenue = serializers.FloatField()
    b2c_revenue = serializers.FloatField()
    b2b_revenue = serializers.FloatField()
    instructor_commission = serializers.FloatField()
    ai_tokens_used = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_courses = serializers.IntegerField()


class TrendPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.FloatField()
    b2c_revenue = serializers.FloatField()
    b2b_revenue = serializers.FloatField()
    ai_tokens_used = serializers.IntegerField()
    new_users = serializers.IntegerField()


class TopCourseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    revenue = serializers.FloatField()
    enrollments = serializers.IntegerField()


class CategoryDistributionSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.FloatField()


class DashboardAnalyticsSerializer(serializers.Serializer):
    summary = AnalyticsSummarySerializer()
    trend = TrendPointSerializer(many=True)
    top_courses = TopCourseSerializer(many=True)
    category_distribution = CategoryDistributionSerializer(many=True)
