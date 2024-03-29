/*
 * parsing/depth.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use crate::non_empty_vec::NonEmptyVec;
use std::mem;

pub type DepthList<L, T> = Vec<DepthItem<L, T>>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DepthItem<L, T> {
    Item(T),
    List(L, DepthList<L, T>),
}

#[derive(Debug)]
struct DepthStack<L, T> {
    finished: Vec<(L, DepthList<L, T>)>,
    stack: NonEmptyVec<(L, Vec<DepthItem<L, T>>)>,
}

impl<L, T> DepthStack<L, T>
where
    L: Copy,
{
    #[inline]
    pub fn new(top_ltype: L) -> Self {
        DepthStack {
            finished: Vec::new(),
            stack: NonEmptyVec::new((top_ltype, Vec::new())),
        }
    }

    pub fn increase_depth(&mut self, ltype: L) {
        self.stack.push((ltype, Vec::new()));
    }

    pub fn decrease_depth(&mut self) {
        let (ltype, list) = self.stack.pop().expect("No depth to pop off!");
        self.push(DepthItem::List(ltype, list));
    }

    pub fn new_list(&mut self, ltype: L) {
        if self.stack.is_single() {
            // This is the last layer, so the pop/push trick doesn't work.
            //
            // Instead, output this entire thing as a finished list tree,
            // then create a new one for the process to continue.
            self.finish_depth_list(Some(ltype));
        } else {
            // We can just decrease and increase to make a new list
            self.decrease_depth();
            self.increase_depth(ltype);
        }
    }

    fn push(&mut self, item: DepthItem<L, T>) {
        self.stack.last_mut().1.push(item);
    }

    #[inline]
    pub fn push_item(&mut self, item: T) {
        self.push(DepthItem::Item(item));
    }

    #[inline]
    pub fn last_type(&self) -> L {
        self.stack.last().0
    }

    fn finish_depth_list(&mut self, new_ltype: Option<L>) {
        // Wrap all opened layers
        // Start at 1 since it's a non-empty vec
        for _ in 1..self.stack.len() {
            self.decrease_depth();
        }

        debug_assert!(
            self.stack.is_single(),
            "Open layers remain after collapsing",
        );

        // Return top-level layer
        let (ltype, list) = {
            // For into_trees(), we don't care what the new ltype is,
            // so we just reuse the last one.
            //
            // But for new_list() we do, we want a new list layer.
            let new_ltype = new_ltype.unwrap_or(self.stack.first().0);

            mem::replace(self.stack.first_mut(), (new_ltype, Vec::new()))
        };

        // Only push if the list has elements
        if !list.is_empty() {
            self.finished.push((ltype, list));
        }
    }

    pub fn into_trees(mut self) -> Vec<(L, DepthList<L, T>)> {
        self.finish_depth_list(None);
        self.finished
    }
}

pub fn process_depths<I, L, T>(top_ltype: L, items: I) -> Vec<(L, DepthList<L, T>)>
where
    I: IntoIterator<Item = (usize, L, T)>,
    L: Copy + PartialEq,
{
    let mut stack = DepthStack::new(top_ltype);

    // The depth value for the previous item
    let mut previous = 0;

    // Iterate through each of the items
    for (depth, ltype, item) in items {
        // Add or remove new depth levels as appropriate,
        // based on what our new depth value is compared
        // to the value in the previous iteration.
        //
        // If previous == depth, then neither of these for loops will run
        // If previous < depth, then only the first will run
        // If previous > depth, then only the second will run

        // Open new levels
        for _ in previous..depth {
            stack.increase_depth(ltype);
        }

        // Close existing levels
        for _ in depth..previous {
            stack.decrease_depth();
        }

        // Create new level if the type doesn't match
        //
        // Here we decrease and increase the depth to close
        // the current layer, then make a new one with the
        // type this item has.
        //
        // We'll keep appending to this remade layer until
        // we hit a different depth or a different type.
        if stack.last_type() != ltype {
            stack.new_list(ltype);
        }

        // Push element and update state
        stack.push_item(item);
        previous = depth;
    }

    stack.into_trees()
}