BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "account_emailaddress" (
	"id"	integer NOT NULL,
	"verified"	bool NOT NULL,
	"primary"	bool NOT NULL,
	"user_id"	bigint NOT NULL,
	"email"	varchar(254) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "account_emailconfirmation" (
	"id"	integer NOT NULL,
	"created"	datetime NOT NULL,
	"sent"	datetime,
	"key"	varchar(64) NOT NULL UNIQUE,
	"email_address_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("email_address_id") REFERENCES "account_emailaddress"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "accounts_instructorprofile" (
	"id"	integer NOT NULL,
	"about"	text NOT NULL,
	"expertise_areas"	text NOT NULL CHECK((JSON_VALID("expertise_areas") OR "expertise_areas" IS NULL)),
	"total_students"	integer NOT NULL,
	"total_courses"	integer NOT NULL,
	"total_reviews"	integer NOT NULL,
	"average_rating"	decimal NOT NULL,
	"total_revenue"	decimal NOT NULL,
	"is_featured"	bool NOT NULL,
	"verified"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"user_id"	bigint NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "accounts_user" (
	"id"	integer NOT NULL,
	"password"	varchar(128) NOT NULL,
	"last_login"	datetime,
	"is_superuser"	bool NOT NULL,
	"username"	varchar(150) NOT NULL UNIQUE,
	"first_name"	varchar(150) NOT NULL,
	"last_name"	varchar(150) NOT NULL,
	"email"	varchar(254) NOT NULL,
	"is_staff"	bool NOT NULL,
	"is_active"	bool NOT NULL,
	"date_joined"	datetime NOT NULL,
	"is_instructor"	bool NOT NULL,
	"email_verified"	bool NOT NULL,
	"profile_photo"	varchar(100),
	"bio"	text NOT NULL,
	"headline"	varchar(200) NOT NULL,
	"website"	varchar(200) NOT NULL,
	"linkedin"	varchar(200) NOT NULL,
	"twitter"	varchar(50) NOT NULL,
	"youtube"	varchar(200) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "accounts_user_groups" (
	"id"	integer NOT NULL,
	"user_id"	bigint NOT NULL,
	"group_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("group_id") REFERENCES "auth_group"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "accounts_user_user_permissions" (
	"id"	integer NOT NULL,
	"user_id"	bigint NOT NULL,
	"permission_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "analytics_coursemetric" (
	"id"	integer NOT NULL,
	"date"	date NOT NULL,
	"views"	integer unsigned NOT NULL CHECK("views" >= 0),
	"revenue"	decimal NOT NULL,
	"new_enrollments"	integer unsigned NOT NULL CHECK("new_enrollments" >= 0),
	"rating_avg"	real NOT NULL,
	"course_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "analytics_dailymetric" (
	"id"	integer NOT NULL,
	"date"	date NOT NULL UNIQUE,
	"new_users"	integer unsigned NOT NULL CHECK("new_users" >= 0),
	"active_users"	integer unsigned NOT NULL CHECK("active_users" >= 0),
	"total_users"	integer unsigned NOT NULL CHECK("total_users" >= 0),
	"total_revenue"	decimal NOT NULL,
	"platform_revenue"	decimal NOT NULL,
	"new_courses"	integer unsigned NOT NULL CHECK("new_courses" >= 0),
	"total_enrollments"	integer unsigned NOT NULL CHECK("total_enrollments" >= 0),
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "auth_group" (
	"id"	integer NOT NULL,
	"name"	varchar(150) NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "auth_group_permissions" (
	"id"	integer NOT NULL,
	"group_id"	integer NOT NULL,
	"permission_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("group_id") REFERENCES "auth_group"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "auth_permission" (
	"id"	integer NOT NULL,
	"content_type_id"	integer NOT NULL,
	"codename"	varchar(100) NOT NULL,
	"name"	varchar(255) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_certification" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"slug"	varchar(200) NOT NULL UNIQUE,
	"level"	varchar(20) NOT NULL,
	"description"	text NOT NULL,
	"price"	decimal NOT NULL,
	"estimated_prep_time"	varchar(50) NOT NULL,
	"pass_rate"	varchar(10) NOT NULL,
	"syllabus"	text NOT NULL CHECK((JSON_VALID("syllabus") OR "syllabus" IS NULL)),
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"provider_id"	bigint NOT NULL,
	"badge_image_url"	varchar(200),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("provider_id") REFERENCES "certification_certificationprovider"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_certificationprovider" (
	"id"	integer NOT NULL,
	"name"	varchar(100) NOT NULL,
	"slug"	varchar(100) NOT NULL UNIQUE,
	"logo"	varchar(100),
	"description"	text NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "certification_exammodule" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"order"	integer unsigned NOT NULL CHECK("order" >= 0),
	"content"	text NOT NULL,
	"video_url"	varchar(200),
	"duration_minutes"	integer unsigned NOT NULL CHECK("duration_minutes" >= 0),
	"certification_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("certification_id") REFERENCES "certification_certification"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_practiceexam" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"duration_minutes"	integer NOT NULL,
	"passing_score"	integer NOT NULL,
	"total_questions"	integer NOT NULL,
	"is_randomized"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"certification_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("certification_id") REFERENCES "certification_certification"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_question" (
	"id"	integer NOT NULL,
	"text"	text NOT NULL,
	"question_type"	varchar(10) NOT NULL,
	"explanation"	text NOT NULL,
	"points"	integer NOT NULL,
	"domain"	varchar(100) NOT NULL,
	"answers"	text NOT NULL CHECK((JSON_VALID("answers") OR "answers" IS NULL)),
	"exam_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("exam_id") REFERENCES "certification_practiceexam"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_usercertificationprogress" (
	"id"	integer NOT NULL,
	"is_completed"	bool NOT NULL,
	"completion_date"	datetime,
	"last_accessed"	datetime NOT NULL,
	"certification_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("certification_id") REFERENCES "certification_certification"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_usercertificationprogress_completed_exams" (
	"id"	integer NOT NULL,
	"usercertificationprogress_id"	bigint NOT NULL,
	"practiceexam_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("practiceexam_id") REFERENCES "certification_practiceexam"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("usercertificationprogress_id") REFERENCES "certification_usercertificationprogress"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "certification_usercertificationprogress_completed_modules" (
	"id"	integer NOT NULL,
	"usercertificationprogress_id"	bigint NOT NULL,
	"exammodule_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("exammodule_id") REFERENCES "certification_exammodule"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("usercertificationprogress_id") REFERENCES "certification_usercertificationprogress"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "core_activitylog" (
	"id"	integer NOT NULL,
	"action"	varchar(50) NOT NULL,
	"message"	text NOT NULL,
	"metadata"	text NOT NULL CHECK((JSON_VALID("metadata") OR "metadata" IS NULL)),
	"created_at"	datetime NOT NULL,
	"user_id"	bigint,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "core_announcement" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"message"	text NOT NULL,
	"announcement_type"	varchar(20) NOT NULL,
	"is_active"	bool NOT NULL,
	"show_on_homepage"	bool NOT NULL,
	"start_date"	datetime NOT NULL,
	"end_date"	datetime,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "core_sitesettings" (
	"id"	integer NOT NULL,
	"site_name"	varchar(100) NOT NULL,
	"tagline"	varchar(200) NOT NULL,
	"site_description"	text NOT NULL,
	"contact_email"	varchar(254) NOT NULL,
	"support_email"	varchar(254) NOT NULL,
	"facebook_url"	varchar(200) NOT NULL,
	"twitter_url"	varchar(200) NOT NULL,
	"instagram_url"	varchar(200) NOT NULL,
	"youtube_url"	varchar(200) NOT NULL,
	"default_platform_fee_percent"	decimal NOT NULL,
	"enable_course_reviews"	bool NOT NULL,
	"enable_qa"	bool NOT NULL,
	"enable_wishlist"	bool NOT NULL,
	"enable_certificates"	bool NOT NULL,
	"maintenance_mode"	bool NOT NULL,
	"maintenance_message"	text NOT NULL,
	"updated_at"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "core_systemkey" (
	"id"	integer NOT NULL,
	"key"	varchar(100) NOT NULL UNIQUE,
	"value"	text NOT NULL,
	"type"	varchar(10) NOT NULL,
	"description"	text NOT NULL,
	"is_public"	bool NOT NULL,
	"updated_at"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "course_announcement" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"content"	text NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"course_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_category" (
	"id"	integer NOT NULL,
	"name"	varchar(100) NOT NULL UNIQUE,
	"slug"	varchar(120) NOT NULL UNIQUE,
	"icon"	varchar(50) NOT NULL,
	"description"	text NOT NULL,
	"order"	integer NOT NULL,
	"is_active"	bool NOT NULL,
	"is_popular"	bool NOT NULL,
	"level"	integer unsigned NOT NULL CHECK("level" >= 0),
	"lft"	integer unsigned NOT NULL CHECK("lft" >= 0),
	"rght"	integer unsigned NOT NULL CHECK("rght" >= 0),
	"tree_id"	integer unsigned NOT NULL CHECK("tree_id" >= 0),
	"parent_id"	bigint,
	"name_vi"	varchar(100),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("parent_id") REFERENCES "course_category"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_course" (
	"id"	integer NOT NULL,
	"uuid"	char(32) NOT NULL UNIQUE,
	"title"	varchar(200) NOT NULL,
	"subtitle"	varchar(200) NOT NULL,
	"slug"	varchar(250) NOT NULL UNIQUE,
	"description"	text NOT NULL,
	"what_you_will_learn"	text NOT NULL CHECK((JSON_VALID("what_you_will_learn") OR "what_you_will_learn" IS NULL)),
	"requirements"	text NOT NULL CHECK((JSON_VALID("requirements") OR "requirements" IS NULL)),
	"target_audience"	text NOT NULL CHECK((JSON_VALID("target_audience") OR "target_audience" IS NULL)),
	"thumbnail"	varchar(100),
	"promo_video_url"	varchar(200) NOT NULL,
	"price"	decimal NOT NULL,
	"discount_price"	decimal,
	"is_free"	bool NOT NULL,
	"language"	varchar(50) NOT NULL,
	"level"	varchar(20) NOT NULL,
	"total_duration"	integer NOT NULL,
	"total_lectures"	integer NOT NULL,
	"total_enrollments"	integer NOT NULL,
	"total_reviews"	integer NOT NULL,
	"average_rating"	decimal NOT NULL,
	"status"	varchar(20) NOT NULL,
	"is_featured"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"published_at"	datetime,
	"category_id"	bigint,
	"instructor_id"	bigint NOT NULL,
	"subcategory_id"	bigint,
	"description_vi"	text,
	"subtitle_vi"	varchar(200),
	"title_vi"	varchar(200),
	"requirements_vi"	text NOT NULL CHECK((JSON_VALID("requirements_vi") OR "requirements_vi" IS NULL)),
	"target_audience_vi"	text NOT NULL CHECK((JSON_VALID("target_audience_vi") OR "target_audience_vi" IS NULL)),
	"what_you_will_learn_vi"	text NOT NULL CHECK((JSON_VALID("what_you_will_learn_vi") OR "what_you_will_learn_vi" IS NULL)),
	"is_active"	bool NOT NULL,
	"deleted_at"	datetime,
	"is_deleted"	bool NOT NULL,
	"congratulations_message"	text NOT NULL,
	"welcome_message"	text NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("category_id") REFERENCES "course_category"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("instructor_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("subcategory_id") REFERENCES "course_subcategory"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_courseresource" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"file"	varchar(100) NOT NULL,
	"file_type"	varchar(50) NOT NULL,
	"file_size"	integer NOT NULL,
	"uploaded_at"	datetime NOT NULL,
	"lecture_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_lecture" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"order"	integer unsigned NOT NULL CHECK("order" >= 0),
	"video_url"	varchar(200) NOT NULL,
	"duration"	integer NOT NULL,
	"content"	text NOT NULL,
	"resources"	text NOT NULL CHECK((JSON_VALID("resources") OR "resources" IS NULL)),
	"is_preview"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"section_id"	bigint NOT NULL,
	"article_content"	text NOT NULL,
	"asset_id"	varchar(255) NOT NULL,
	"lecture_type"	varchar(20) NOT NULL,
	"status"	varchar(20) NOT NULL,
	"video_source"	varchar(20) NOT NULL,
	"admin_note"	text NOT NULL,
	"published_at"	datetime,
	"video_file"	varchar(100),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("section_id") REFERENCES "course_section"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_quizanswer" (
	"id"	integer NOT NULL,
	"answer_text"	varchar(255) NOT NULL,
	"is_correct"	bool NOT NULL,
	"question_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("question_id") REFERENCES "course_quizquestion"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_quizquestion" (
	"id"	integer NOT NULL,
	"question_text"	text NOT NULL,
	"explanation"	text NOT NULL,
	"order"	integer unsigned NOT NULL CHECK("order" >= 0),
	"lecture_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_section" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"objective"	text NOT NULL,
	"order"	integer unsigned NOT NULL CHECK("order" >= 0),
	"course_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "course_subcategory" (
	"id"	integer NOT NULL,
	"name"	varchar(100) NOT NULL,
	"slug"	varchar(120) NOT NULL UNIQUE,
	"description"	text NOT NULL,
	"order"	integer NOT NULL,
	"is_active"	bool NOT NULL,
	"category_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("category_id") REFERENCES "course_category"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "django_admin_log" (
	"id"	integer NOT NULL,
	"object_id"	text,
	"object_repr"	varchar(200) NOT NULL,
	"action_flag"	smallint unsigned NOT NULL CHECK("action_flag" >= 0),
	"change_message"	text NOT NULL,
	"content_type_id"	integer,
	"user_id"	bigint NOT NULL,
	"action_time"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "django_content_type" (
	"id"	integer NOT NULL,
	"app_label"	varchar(100) NOT NULL,
	"model"	varchar(100) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "django_migrations" (
	"id"	integer NOT NULL,
	"app"	varchar(255) NOT NULL,
	"name"	varchar(255) NOT NULL,
	"applied"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "django_session" (
	"session_key"	varchar(40) NOT NULL,
	"session_data"	text NOT NULL,
	"expire_date"	datetime NOT NULL,
	PRIMARY KEY("session_key")
);
CREATE TABLE IF NOT EXISTS "organization_businesslead" (
	"id"	integer NOT NULL,
	"full_name"	varchar(255) NOT NULL,
	"email"	varchar(254) NOT NULL,
	"company_name"	varchar(255) NOT NULL,
	"team_size"	varchar(50) NOT NULL,
	"message"	text NOT NULL,
	"status"	varchar(20) NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"request_type"	varchar(20) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "organization_organization" (
	"id"	integer NOT NULL,
	"name"	varchar(255) NOT NULL,
	"slug"	varchar(255) NOT NULL UNIQUE,
	"domain"	varchar(255),
	"subscription_plan"	varchar(20) NOT NULL,
	"max_users"	integer NOT NULL,
	"is_active"	bool NOT NULL,
	"logo"	varchar(100),
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "organization_organizationmember" (
	"id"	integer NOT NULL,
	"role"	varchar(20) NOT NULL,
	"is_active"	bool NOT NULL,
	"date_joined"	datetime NOT NULL,
	"organization_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	"team_id"	bigint,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("organization_id") REFERENCES "organization_organization"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("team_id") REFERENCES "organization_team"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "organization_team" (
	"id"	integer NOT NULL,
	"name"	varchar(255) NOT NULL,
	"description"	text NOT NULL,
	"created_at"	datetime NOT NULL,
	"organization_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("organization_id") REFERENCES "organization_organization"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "payments_coupon" (
	"id"	integer NOT NULL,
	"code"	varchar(50) NOT NULL UNIQUE,
	"discount_type"	varchar(10) NOT NULL,
	"discount_value"	decimal NOT NULL,
	"max_uses"	integer,
	"current_uses"	integer NOT NULL,
	"valid_from"	datetime NOT NULL,
	"valid_until"	datetime NOT NULL,
	"is_active"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"course_id"	bigint,
	"created_by_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("created_by_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "payments_instructorpayout" (
	"id"	integer NOT NULL,
	"period_year"	integer NOT NULL,
	"period_month"	integer NOT NULL,
	"total_revenue"	decimal NOT NULL,
	"platform_fee"	decimal NOT NULL,
	"payout_amount"	decimal NOT NULL,
	"payment_method"	varchar(50) NOT NULL,
	"payment_reference"	varchar(200) NOT NULL,
	"status"	varchar(20) NOT NULL,
	"notes"	text NOT NULL,
	"created_at"	datetime NOT NULL,
	"paid_at"	datetime,
	"instructor_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("instructor_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "payments_order" (
	"id"	integer NOT NULL,
	"order_number"	varchar(50) NOT NULL UNIQUE,
	"total_amount"	decimal NOT NULL,
	"discount_amount"	decimal NOT NULL,
	"final_amount"	decimal NOT NULL,
	"status"	varchar(20) NOT NULL,
	"payment_provider_session_id"	varchar(255) NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "payments_orderitem" (
	"id"	integer NOT NULL,
	"price"	decimal NOT NULL,
	"course_id"	bigint NOT NULL,
	"order_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("order_id") REFERENCES "payments_order"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "payments_transaction" (
	"id"	integer NOT NULL,
	"transaction_id"	varchar(200) NOT NULL UNIQUE,
	"gross_amount"	decimal NOT NULL,
	"platform_fee_percent"	decimal NOT NULL,
	"platform_fee"	decimal NOT NULL,
	"instructor_revenue"	decimal NOT NULL,
	"payment_method"	varchar(20) NOT NULL,
	"payment_provider_id"	varchar(200) NOT NULL,
	"coupon_code"	varchar(50) NOT NULL,
	"discount_amount"	decimal NOT NULL,
	"status"	varchar(20) NOT NULL,
	"refund_reason"	text NOT NULL,
	"refunded_at"	datetime,
	"created_at"	datetime NOT NULL,
	"completed_at"	datetime,
	"course_id"	bigint NOT NULL,
	"enrollment_id"	bigint NOT NULL UNIQUE,
	"student_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("enrollment_id") REFERENCES "result_enrollment"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("student_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "reports_report" (
	"id"	integer NOT NULL,
	"object_id"	integer unsigned NOT NULL CHECK("object_id" >= 0),
	"reason"	varchar(50) NOT NULL,
	"description"	text NOT NULL,
	"status"	varchar(20) NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"assigned_to_id"	bigint,
	"content_type_id"	integer NOT NULL,
	"reporter_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("assigned_to_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("reporter_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "reports_reportlog" (
	"id"	integer NOT NULL,
	"action"	varchar(50) NOT NULL,
	"note"	text NOT NULL,
	"created_at"	datetime NOT NULL,
	"actor_id"	bigint,
	"report_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("actor_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("report_id") REFERENCES "reports_report"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_answer" (
	"id"	integer NOT NULL,
	"answer"	text NOT NULL,
	"is_instructor_answer"	bool NOT NULL,
	"upvote_count"	integer NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"user_id"	bigint NOT NULL,
	"question_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("question_id") REFERENCES "result_question"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_enrollment" (
	"id"	integer NOT NULL,
	"price_paid"	decimal NOT NULL,
	"payment_method"	varchar(50) NOT NULL,
	"transaction_id"	varchar(200) NOT NULL,
	"progress_percent"	decimal NOT NULL,
	"enrolled_at"	datetime NOT NULL,
	"last_accessed"	datetime NOT NULL,
	"completed_at"	datetime,
	"certificate_issued"	bool NOT NULL,
	"course_id"	bigint NOT NULL,
	"last_accessed_lecture_id"	bigint,
	"student_id"	bigint NOT NULL,
	"certificate_number"	varchar(100) UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("last_accessed_lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("student_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_lectureprogress" (
	"id"	integer NOT NULL,
	"completed"	bool NOT NULL,
	"last_position"	integer NOT NULL,
	"watch_count"	integer NOT NULL,
	"first_watched"	datetime NOT NULL,
	"last_watched"	datetime NOT NULL,
	"completed_at"	datetime,
	"enrollment_id"	bigint NOT NULL,
	"lecture_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("enrollment_id") REFERENCES "result_enrollment"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_note" (
	"id"	integer NOT NULL,
	"content"	text NOT NULL,
	"timestamp"	integer NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"lecture_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_question" (
	"id"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"question"	text NOT NULL,
	"timestamp"	integer,
	"is_answered"	bool NOT NULL,
	"answer_count"	integer NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"course_id"	bigint NOT NULL,
	"lecture_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("lecture_id") REFERENCES "course_lecture"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_review" (
	"id"	integer NOT NULL,
	"rating"	integer NOT NULL,
	"title"	varchar(200) NOT NULL,
	"comment"	text NOT NULL,
	"helpful_count"	integer NOT NULL,
	"not_helpful_count"	integer NOT NULL,
	"is_featured"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"updated_at"	datetime NOT NULL,
	"course_id"	bigint NOT NULL,
	"enrollment_id"	bigint NOT NULL UNIQUE,
	"student_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("enrollment_id") REFERENCES "result_enrollment"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("student_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_reviewhelpful" (
	"id"	integer NOT NULL,
	"is_helpful"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"review_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("review_id") REFERENCES "result_review"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "result_wishlist" (
	"id"	integer NOT NULL,
	"added_at"	datetime NOT NULL,
	"course_id"	bigint NOT NULL,
	"user_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("course_id") REFERENCES "course_course"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "socialaccount_socialaccount" (
	"id"	integer NOT NULL,
	"provider"	varchar(200) NOT NULL,
	"uid"	varchar(191) NOT NULL,
	"last_login"	datetime NOT NULL,
	"date_joined"	datetime NOT NULL,
	"user_id"	bigint NOT NULL,
	"extra_data"	text NOT NULL CHECK((JSON_VALID("extra_data") OR "extra_data" IS NULL)),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "accounts_user"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "socialaccount_socialapp" (
	"id"	integer NOT NULL,
	"provider"	varchar(30) NOT NULL,
	"name"	varchar(40) NOT NULL,
	"client_id"	varchar(191) NOT NULL,
	"secret"	varchar(191) NOT NULL,
	"key"	varchar(191) NOT NULL,
	"provider_id"	varchar(200) NOT NULL,
	"settings"	text NOT NULL CHECK((JSON_VALID("settings") OR "settings" IS NULL)),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "socialaccount_socialtoken" (
	"id"	integer NOT NULL,
	"token"	text NOT NULL,
	"token_secret"	text NOT NULL,
	"expires_at"	datetime,
	"account_id"	integer NOT NULL,
	"app_id"	integer,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("account_id") REFERENCES "socialaccount_socialaccount"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("app_id") REFERENCES "socialaccount_socialapp"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX IF NOT EXISTS "account_emailaddress_email_03be32b2" ON "account_emailaddress" (
	"email"
);
CREATE INDEX IF NOT EXISTS "account_emailaddress_user_id_2c513194" ON "account_emailaddress" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "account_emailaddress_user_id_email_987c8728_uniq" ON "account_emailaddress" (
	"user_id",
	"email"
);
CREATE INDEX IF NOT EXISTS "account_emailconfirmation_email_address_id_5b7f8c58" ON "account_emailconfirmation" (
	"email_address_id"
);
CREATE INDEX IF NOT EXISTS "accounts_user_groups_group_id_bd11a704" ON "accounts_user_groups" (
	"group_id"
);
CREATE INDEX IF NOT EXISTS "accounts_user_groups_user_id_52b62117" ON "accounts_user_groups" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "accounts_user_groups_user_id_group_id_59c0b32f_uniq" ON "accounts_user_groups" (
	"user_id",
	"group_id"
);
CREATE INDEX IF NOT EXISTS "accounts_user_user_permissions_permission_id_113bb443" ON "accounts_user_user_permissions" (
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "accounts_user_user_permissions_user_id_e4f0a161" ON "accounts_user_user_permissions" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "accounts_user_user_permissions_user_id_permission_id_2ab516c2_uniq" ON "accounts_user_user_permissions" (
	"user_id",
	"permission_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "analytics_coursemetric_course_id_date_7a6a284f_uniq" ON "analytics_coursemetric" (
	"course_id",
	"date"
);
CREATE INDEX IF NOT EXISTS "analytics_coursemetric_course_id_e928fc92" ON "analytics_coursemetric" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "analytics_coursemetric_date_52bb6893" ON "analytics_coursemetric" (
	"date"
);
CREATE INDEX IF NOT EXISTS "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" (
	"group_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" (
	"group_id",
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" (
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "auth_permission_content_type_id_2f476e4b" ON "auth_permission" (
	"content_type_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" (
	"content_type_id",
	"codename"
);
CREATE INDEX IF NOT EXISTS "certification_certification_provider_id_23fbaa5e" ON "certification_certification" (
	"provider_id"
);
CREATE INDEX IF NOT EXISTS "certification_exammodule_certification_id_51b442fb" ON "certification_exammodule" (
	"certification_id"
);
CREATE INDEX IF NOT EXISTS "certification_practiceexam_certification_id_b47ad57c" ON "certification_practiceexam" (
	"certification_id"
);
CREATE INDEX IF NOT EXISTS "certification_question_exam_id_dffaeedd" ON "certification_question" (
	"exam_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_certification_id_8f9c8993" ON "certification_usercertificationprogress" (
	"certification_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_exams_practiceexam_id_a85968bc" ON "certification_usercertificationprogress_completed_exams" (
	"practiceexam_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_exams_usercertificationprogress_id_5ed96c42" ON "certification_usercertificationprogress_completed_exams" (
	"usercertificationprogress_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_exams_usercertificationprogress_id_practiceexam_id_4a7ce6b6_uniq" ON "certification_usercertificationprogress_completed_exams" (
	"usercertificationprogress_id",
	"practiceexam_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_modules_exammodule_id_f59d6b42" ON "certification_usercertificationprogress_completed_modules" (
	"exammodule_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_modules_usercertificationprogress_id_61f651c9" ON "certification_usercertificationprogress_completed_modules" (
	"usercertificationprogress_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "certification_usercertificationprogress_completed_modules_usercertificationprogress_id_exammodule_id_4dc49245_uniq" ON "certification_usercertificationprogress_completed_modules" (
	"usercertificationprogress_id",
	"exammodule_id"
);
CREATE INDEX IF NOT EXISTS "certification_usercertificationprogress_user_id_7ffd9489" ON "certification_usercertificationprogress" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "certification_usercertificationprogress_user_id_certification_id_a6cabaec_uniq" ON "certification_usercertificationprogress" (
	"user_id",
	"certification_id"
);
CREATE INDEX IF NOT EXISTS "core_activi_action_a01617_idx" ON "core_activitylog" (
	"action",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "core_activi_created_3d0bd9_idx" ON "core_activitylog" (
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "core_activitylog_user_id_8705e516" ON "core_activitylog" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "course_anno_course__d8bc24_idx" ON "course_announcement" (
	"course_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "course_announcement_course_id_7364f48e" ON "course_announcement" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "course_announcement_user_id_0781d910" ON "course_announcement" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "course_category_parent_id_9dd51d36" ON "course_category" (
	"parent_id"
);
CREATE INDEX IF NOT EXISTS "course_category_tree_id_35edc622" ON "course_category" (
	"tree_id"
);
CREATE INDEX IF NOT EXISTS "course_cour_average_35280c_idx" ON "course_course" (
	"average_rating"	DESC
);
CREATE INDEX IF NOT EXISTS "course_cour_categor_26bb4d_idx" ON "course_course" (
	"category_id",
	"status"
);
CREATE INDEX IF NOT EXISTS "course_cour_status_e51eb2_idx" ON "course_course" (
	"status",
	"is_featured"
);
CREATE INDEX IF NOT EXISTS "course_cour_total_e_ba7a65_idx" ON "course_course" (
	"total_enrollments"	DESC
);
CREATE INDEX IF NOT EXISTS "course_course_category_id_0b2127b9" ON "course_course" (
	"category_id"
);
CREATE INDEX IF NOT EXISTS "course_course_instructor_id_0e036d8e" ON "course_course" (
	"instructor_id"
);
CREATE INDEX IF NOT EXISTS "course_course_subcategory_id_6e46ef76" ON "course_course" (
	"subcategory_id"
);
CREATE INDEX IF NOT EXISTS "course_courseresource_lecture_id_0dce9f48" ON "course_courseresource" (
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "course_lecture_section_id_2ee53690" ON "course_lecture" (
	"section_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "course_lecture_section_id_order_e33aba38_uniq" ON "course_lecture" (
	"section_id",
	"order"
);
CREATE INDEX IF NOT EXISTS "course_quizanswer_question_id_f03df19c" ON "course_quizanswer" (
	"question_id"
);
CREATE INDEX IF NOT EXISTS "course_quizquestion_lecture_id_dcc9e725" ON "course_quizquestion" (
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "course_section_course_id_b17c56a1" ON "course_section" (
	"course_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "course_section_course_id_order_265248db_uniq" ON "course_section" (
	"course_id",
	"order"
);
CREATE INDEX IF NOT EXISTS "course_subcategory_category_id_19e345e8" ON "course_subcategory" (
	"category_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "course_subcategory_category_id_name_0872369f_uniq" ON "course_subcategory" (
	"category_id",
	"name"
);
CREATE INDEX IF NOT EXISTS "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" (
	"content_type_id"
);
CREATE INDEX IF NOT EXISTS "django_admin_log_user_id_c564eba6" ON "django_admin_log" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" (
	"app_label",
	"model"
);
CREATE INDEX IF NOT EXISTS "django_session_expire_date_a5c62663" ON "django_session" (
	"expire_date"
);
CREATE INDEX IF NOT EXISTS "organization_organizationmember_organization_id_9fc8c112" ON "organization_organizationmember" (
	"organization_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "organization_organizationmember_organization_id_user_id_0931ac98_uniq" ON "organization_organizationmember" (
	"organization_id",
	"user_id"
);
CREATE INDEX IF NOT EXISTS "organization_organizationmember_team_id_76b88243" ON "organization_organizationmember" (
	"team_id"
);
CREATE INDEX IF NOT EXISTS "organization_organizationmember_user_id_0667f9ab" ON "organization_organizationmember" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "organization_team_organization_id_6b23f2d7" ON "organization_team" (
	"organization_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "organization_team_organization_id_name_53360634_uniq" ON "organization_team" (
	"organization_id",
	"name"
);
CREATE INDEX IF NOT EXISTS "payments_coupon_course_id_1a02422b" ON "payments_coupon" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "payments_coupon_created_by_id_feb2783c" ON "payments_coupon" (
	"created_by_id"
);
CREATE INDEX IF NOT EXISTS "payments_instructorpayout_instructor_id_789af9e2" ON "payments_instructorpayout" (
	"instructor_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "payments_instructorpayout_instructor_id_period_year_period_month_2b1629bb_uniq" ON "payments_instructorpayout" (
	"instructor_id",
	"period_year",
	"period_month"
);
CREATE INDEX IF NOT EXISTS "payments_order_user_id_50e0f630" ON "payments_order" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "payments_orderitem_course_id_f9f71ca9" ON "payments_orderitem" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "payments_orderitem_order_id_4cc4fe53" ON "payments_orderitem" (
	"order_id"
);
CREATE INDEX IF NOT EXISTS "payments_tr_course__c74fa0_idx" ON "payments_transaction" (
	"course_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "payments_tr_status_7127e3_idx" ON "payments_transaction" (
	"status",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "payments_tr_student_c823f1_idx" ON "payments_transaction" (
	"student_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "payments_transaction_course_id_348d4170" ON "payments_transaction" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "payments_transaction_student_id_970247d7" ON "payments_transaction" (
	"student_id"
);
CREATE INDEX IF NOT EXISTS "reports_rep_status_7dd5e5_idx" ON "reports_report" (
	"status",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "reports_report_assigned_to_id_5a6b5eea" ON "reports_report" (
	"assigned_to_id"
);
CREATE INDEX IF NOT EXISTS "reports_report_content_type_id_f40e73c6" ON "reports_report" (
	"content_type_id"
);
CREATE INDEX IF NOT EXISTS "reports_report_reporter_id_d54be306" ON "reports_report" (
	"reporter_id"
);
CREATE INDEX IF NOT EXISTS "reports_reportlog_actor_id_619cb6ea" ON "reports_reportlog" (
	"actor_id"
);
CREATE INDEX IF NOT EXISTS "reports_reportlog_report_id_b6716fee" ON "reports_reportlog" (
	"report_id"
);
CREATE INDEX IF NOT EXISTS "result_answer_question_id_3de68ecf" ON "result_answer" (
	"question_id"
);
CREATE INDEX IF NOT EXISTS "result_answer_user_id_523c0a45" ON "result_answer" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "result_enro_course__53f544_idx" ON "result_enrollment" (
	"course_id",
	"enrolled_at"	DESC
);
CREATE INDEX IF NOT EXISTS "result_enro_student_955660_idx" ON "result_enrollment" (
	"student_id",
	"enrolled_at"	DESC
);
CREATE INDEX IF NOT EXISTS "result_enrollment_course_id_d2b7a65b" ON "result_enrollment" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_enrollment_last_accessed_lecture_id_850bb104" ON "result_enrollment" (
	"last_accessed_lecture_id"
);
CREATE INDEX IF NOT EXISTS "result_enrollment_student_id_5aa71fae" ON "result_enrollment" (
	"student_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "result_enrollment_student_id_course_id_630b91db_uniq" ON "result_enrollment" (
	"student_id",
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_lect_enrollm_2d4d67_idx" ON "result_lectureprogress" (
	"enrollment_id",
	"completed"
);
CREATE INDEX IF NOT EXISTS "result_lectureprogress_enrollment_id_b63a4800" ON "result_lectureprogress" (
	"enrollment_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "result_lectureprogress_enrollment_id_lecture_id_70a3bdad_uniq" ON "result_lectureprogress" (
	"enrollment_id",
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "result_lectureprogress_lecture_id_b7347f56" ON "result_lectureprogress" (
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "result_note_lecture_37575b_idx" ON "result_note" (
	"lecture_id",
	"timestamp"
);
CREATE INDEX IF NOT EXISTS "result_note_lecture_id_af34a62d" ON "result_note" (
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "result_note_user_id_8e831b23" ON "result_note" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "result_ques_course__082844_idx" ON "result_question" (
	"course_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "result_ques_lecture_04e410_idx" ON "result_question" (
	"lecture_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "result_question_course_id_6ce082d5" ON "result_question" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_question_lecture_id_9de2f20b" ON "result_question" (
	"lecture_id"
);
CREATE INDEX IF NOT EXISTS "result_question_user_id_5fbbe4a0" ON "result_question" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "result_revi_course__6c55c6_idx" ON "result_review" (
	"course_id",
	"created_at"	DESC
);
CREATE INDEX IF NOT EXISTS "result_revi_course__6f4d88_idx" ON "result_review" (
	"course_id",
	"helpful_count"	DESC
);
CREATE INDEX IF NOT EXISTS "result_review_course_id_1db0ffa7" ON "result_review" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_review_student_id_38896bfe" ON "result_review" (
	"student_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "result_review_student_id_course_id_d48cb8b3_uniq" ON "result_review" (
	"student_id",
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_reviewhelpful_review_id_c847a6fa" ON "result_reviewhelpful" (
	"review_id"
);
CREATE INDEX IF NOT EXISTS "result_reviewhelpful_user_id_62460327" ON "result_reviewhelpful" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "result_reviewhelpful_user_id_review_id_61c39cf6_uniq" ON "result_reviewhelpful" (
	"user_id",
	"review_id"
);
CREATE INDEX IF NOT EXISTS "result_wishlist_course_id_a1bcfbb6" ON "result_wishlist" (
	"course_id"
);
CREATE INDEX IF NOT EXISTS "result_wishlist_user_id_7559c0f0" ON "result_wishlist" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "socialaccount_socialaccount_provider_uid_fc810c6e_uniq" ON "socialaccount_socialaccount" (
	"provider",
	"uid"
);
CREATE INDEX IF NOT EXISTS "socialaccount_socialaccount_user_id_8146e70c" ON "socialaccount_socialaccount" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "socialaccount_socialtoken_account_id_951f210e" ON "socialaccount_socialtoken" (
	"account_id"
);
CREATE INDEX IF NOT EXISTS "socialaccount_socialtoken_app_id_636a42d7" ON "socialaccount_socialtoken" (
	"app_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq" ON "socialaccount_socialtoken" (
	"app_id",
	"account_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "unique_primary_email" ON "account_emailaddress" (
	"user_id",
	"primary"
) WHERE "primary";
CREATE UNIQUE INDEX IF NOT EXISTS "unique_verified_email" ON "account_emailaddress" (
	"email"
) WHERE "verified";
COMMIT;
