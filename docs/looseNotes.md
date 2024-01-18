# System start

For each **product**, load the amount of the product available in all of the **warehouses**. This will be the *available to be put into cart* count. Also, initialize *already in a cart* count to **0**.

# Customer loads the shopping page

For each **product**, show the *available to be put into the cart* as the *available* count.

# Customer puts a product in the cart

When a **customer** puts a product into a **cart**, then increment the *already in a cart* count for this product. If, due to the state change happening in the background, the *available* is **0** or less, then don't update the cart and return the page to user with the alert.

# Customer finalizing the purchase

When a **customer** finishes the purchase, then for each **product** they have chosen, **warehouse**s are sorted and the number of the product stored in the warehouse is reduced by the amount the customer has purchased. If this number exceeds the amount of the product that is stored in the warehouse, then the difference is reduced from the next warehouse in the list. This continues until the number is satisfied.

# Supply arrives

When **supply** arrives for a **product**, then the *available to be put into the cart* count is updated.

# Clerk accepts client request

When **clerk** accepts a **client request** for a **product**, then the *available to be put into the cart* and *available* are reduced by the amount from the request. If this would bring the *available* below **0**, then the first request of a **customer** that has this product in the cart (be it adding new item to cart, checking / modifying the cart or finalizing the transaction) should fail and reduce the amount of the product in the cart by the number below **0** of the *available* count. If it is not enough, then the next (different) customer request should have the same effect until the *available* count is at least **0** again.