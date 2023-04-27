import AO3

search = AO3.Search(any_field="", tags="", kudos=AO3.utils.Constraint(30, 5000), fandoms="Original Work", word_count=AO3.utils.Constraint(5000, 15000))
search.update()
print(search.total_results)

search.results[4].id
work = AO3.Work(search.results[4].id)

for chapter in work.chapters:

text = work.chapters[0].text