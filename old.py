
'''reset_tables()

for year in [2022, 2023, 2024]:
    seeds = get_seeds(year)
    stats = get_school_stats(year)

    seeds['TeamName'] = seeds['TeamName'].apply(normalize_name)
    stats['School'] = stats['School'].apply(normalize_name)

    merged = pd.merge(seeds, stats, left_on='TeamName', right_on='School')
    merged = merged.drop(columns=['School'])
    merged = merged.rename(columns={'TeamName': 'team_name', 'Seed': 'seed'})
    merged['year'] = year

    print(f"Inserting {len(merged)} rows for {year}")
    insert_teams(merged)

    for team_name, region in get_team_regions(year):
        name = normalize_name(team_name)
        update_region(name, region, year)

print("Done!")

teams = get_teams(2024)
avg_off, avg_def = get_averages(2024)

win_counts_total = Counter()
final_four_total = Counter()
champ_counts = Counter()

for i in range(1000):
    win_counts, champ_id = simulate_tournament(teams, avg_off, avg_def, method='simpy')
    for team_id, wins in win_counts.items():
        if wins >= 4:
            win_counts_total[team_id] += 1
        if wins >= 5:
            final_four_total[team_id] += 1
    champ_counts[champ_id] += 1

team_lookup = {t['team_id']: t['name'] for t in teams}

print("SimPy Top 10 (4+ wins):")
for team_id, count in win_counts_total.most_common(10):
    name = team_lookup.get(team_id, f"Unknown ({team_id})")
    final_four_pct = final_four_total.get(team_id, 0) / 10
    champ_pct = champ_counts.get(team_id, 0) / 10
    print(f"  {name}: {count/10:.1f}% in final 4 - {final_four_pct:.1f}% in championship game - {champ_pct:.1f}% champions")
'''