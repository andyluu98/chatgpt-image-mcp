from cgimg.research.scoring import score_finding, rank, cluster


def test_score_rewards_engagement():
    low = {"engagement": {"views": 10, "likes": 1, "comments": 0}, "published_at": "20260101"}
    high = {"engagement": {"views": 100000, "likes": 5000, "comments": 300}, "published_at": "20260101"}
    assert score_finding(high) > score_finding(low)


def test_rank_sorts_desc():
    items = [{"engagement": {"views": 10}}, {"engagement": {"views": 999}}]
    ranked = rank(items)
    assert ranked[0]["engagement"]["views"] == 999


def test_cluster_merges_similar_titles():
    items = [
        {"title": "VN-Index tăng mạnh phiên hôm nay", "url": "a", "engagement": {"views": 5}},
        {"title": "VN-Index tăng mạnh phiên hôm nay!!!", "url": "b", "engagement": {"views": 9}},
        {"title": "Giá vàng lập đỉnh", "url": "c", "engagement": {"views": 3}},
    ]
    clusters = cluster(items)
    assert len(clusters) == 2


def test_cluster_keeps_highest_engagement_as_lead():
    items = [
        {"title": "Cổ phiếu thép bứt phá", "url": "a", "engagement": {"views": 5}},
        {"title": "Cổ phiếu thép bứt phá mạnh", "url": "b", "engagement": {"views": 50}},
    ]
    clusters = cluster(items)
    assert clusters[0]["lead"]["url"] == "b"
