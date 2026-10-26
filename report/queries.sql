-- name: base
-- Common CTE: the only client-population filter, used by every report query.
WITH eligible_users AS (
    SELECT id, participant_code, date_joined, prev_promo_participant
    FROM promo_user
    WHERE NOT is_staff AND (participant_code IS NULL OR NOT (participant_code = ANY(%(excluded_codes)s::text[])))
), weeks AS (
    SELECT * FROM unnest(%(week_numbers)s::integer[], %(week_starts)s::date[], %(week_ends)s::date[])
        AS w(week, start_day, end_day)
), receipts AS (
    SELECT r.id, r.user_id, r.status, r.reject_reason, r.points, r.prize_amount,
           (r.created_at AT TIME ZONE %(timezone)s)::date AS day
    FROM promo_receipt r JOIN eligible_users u ON u.id = r.user_id
    WHERE r.created_at >= %(start)s AND r.created_at < %(end)s
), first_receipts AS (
    -- Entire history, all statuses; never restricted to the reporting period.
    SELECT r.user_id, (MIN(r.created_at) AT TIME ZONE %(timezone)s)::date AS first_day
    FROM promo_receipt r JOIN (SELECT DISTINCT user_id FROM receipts) u ON u.user_id = r.user_id
    GROUP BY r.user_id
), packs AS (
    SELECT r.id AS receipt_id, r.day, p.pack_format, i.quantity
    FROM receipts r JOIN promo_receiptitem i ON i.receipt_id = r.id
    JOIN promo_product p ON p.id = i.product_id
    WHERE r.status = 'accepted'
)

-- name: weekly
SELECT w.week,
    (SELECT COUNT(*) FROM eligible_users u
     WHERE (u.date_joined AT TIME ZONE %(timezone)s)::date >= w.start_day
       AND (u.date_joined AT TIME ZONE %(timezone)s)::date < w.end_day) AS registrations,
    (SELECT COUNT(DISTINCT user_id) FROM receipts WHERE day >= w.start_day AND day < w.end_day) AS participants,
    (SELECT COUNT(*) FROM first_receipts WHERE first_day >= w.start_day AND first_day < w.end_day) AS new_participants,
    (SELECT COUNT(*) FROM first_receipts f JOIN eligible_users u ON u.id=f.user_id
     WHERE first_day >= w.start_day AND first_day < w.end_day AND u.prev_promo_participant) AS previous_promo,
    COUNT(r.id) AS uploaded,
    COUNT(r.id) FILTER (WHERE r.status='accepted') AS accepted,
    (SELECT COALESCE(SUM(quantity),0) FROM packs WHERE day >= w.start_day AND day < w.end_day) AS packs,
    COUNT(r.id) FILTER (WHERE r.status='rejected') AS rejected,
    COUNT(r.id) FILTER (WHERE r.status='pending') AS pending
FROM weeks w LEFT JOIN receipts r ON r.day >= w.start_day AND r.day < w.end_day
GROUP BY w.week,w.start_day,w.end_day ORDER BY w.week;

-- name: daily
SELECT d::date AS day,
    (SELECT COUNT(*) FROM eligible_users u WHERE (u.date_joined AT TIME ZONE %(timezone)s)::date=d::date) AS registrations,
    (SELECT COUNT(*) FROM receipts r WHERE r.day=d::date AND r.status='accepted') AS accepted
FROM generate_series((%(start)s AT TIME ZONE %(timezone)s)::date,
     (%(end)s AT TIME ZONE %(timezone)s)::date - 1, INTERVAL '1 day') d ORDER BY d;

-- name: reasons
SELECT w.week,r.reject_reason,COUNT(*) AS count FROM weeks w
JOIN receipts r ON r.day>=w.start_day AND r.day<w.end_day
WHERE r.status='rejected' GROUP BY w.week,r.reject_reason ORDER BY w.week,r.reject_reason;

-- name: sku
SELECT pack_format,SUM(quantity) AS quantity FROM packs GROUP BY pack_format ORDER BY pack_format;

-- name: participants
SELECT u.participant_code, (u.date_joined AT TIME ZONE %(timezone)s)::date AS registration_day,
    COUNT(*) AS uploaded,COUNT(*) FILTER(WHERE r.status='accepted') AS accepted,
    SUM(r.points) AS points,COALESCE(SUM(r.prize_amount),0) AS prizes,
    u.prev_promo_participant AS previous_promo
FROM eligible_users u JOIN receipts r ON r.user_id=u.id
GROUP BY u.id,u.participant_code,u.date_joined,u.prev_promo_participant ORDER BY u.participant_code;

-- name: totals
SELECT
    (SELECT COUNT(*) FROM eligible_users WHERE date_joined>=%(start)s AND date_joined<%(end)s) AS registrations,
    COUNT(DISTINCT user_id) AS participants,COUNT(*) AS uploaded,
    COUNT(*) FILTER(WHERE status='accepted') AS accepted,
    COUNT(*) FILTER(WHERE status='rejected') AS rejected,
    COUNT(*) FILTER(WHERE status='pending') AS pending,
    (SELECT COALESCE(SUM(quantity),0) FROM packs) AS packs,
    COALESCE(SUM(points),0) AS points,COALESCE(SUM(prize_amount),0) AS prizes
FROM receipts;

-- name: quality
SELECT
    (SELECT COUNT(*) FROM eligible_users u WHERE EXISTS (SELECT 1 FROM receipts r WHERE r.user_id=u.id)
     AND (participant_code IS NULL OR participant_code !~ '^[0-9]{20}$')) AS invalid_codes,
    (SELECT COUNT(*) FROM (SELECT participant_code FROM eligible_users u
     WHERE EXISTS (SELECT 1 FROM receipts r WHERE r.user_id=u.id) GROUP BY participant_code HAVING COUNT(*)>1) x) AS duplicate_codes,
    COUNT(*) FILTER(WHERE status IS NULL OR status NOT IN ('accepted','rejected','pending')) AS unknown_status,
    COUNT(*) FILTER(WHERE points<0 OR prize_amount<0 OR points IS NULL) AS invalid_rewards,
    COUNT(*) FILTER(WHERE status<>'accepted' AND (points<>0 OR COALESCE(prize_amount,0)<>0)) AS nonaccepted_rewards,
    COUNT(*) FILTER(WHERE status='accepted' AND NOT EXISTS(SELECT 1 FROM promo_receiptitem i WHERE i.receipt_id=receipts.id)) AS accepted_without_items,
    COUNT(*) FILTER(WHERE status='rejected' AND (reject_reason IS NULL OR TRIM(reject_reason)='')) AS empty_rejection_reason,
    (SELECT COUNT(*) FROM packs WHERE quantity<=0) AS invalid_quantity,
    (SELECT COUNT(*) FROM receipts r JOIN eligible_users u ON u.id=r.user_id
     WHERE r.day<(u.date_joined AT TIME ZONE %(timezone)s)::date) AS receipt_before_registration_day
FROM receipts;

